"""
A webdriver/selenium based scraper for San Francisco Board of Supervisors
voting data.
    - Troy Deck (troy.deque@gmail.com)
"""
from selenium import webdriver
from datetime import date
import argparse
import time
import db

#############
# Constants #
#############
PATIENCE = 2 # Seconds to wait after executing a JS action
VOTING_GRID_ID = 'ctl00_ContentPlaceHolder1_gridVoting_ctl00'

#
# Main scraping functions
#
def scrape_proposal_page(browser, proposal_url):
    """
    Navigates to the page giving details about a piece of legislation, scrapes
    that data, and adds a model to the database session. Returns the new DB
    model.
    """
    browser.get(proposal_url)

    file_number = int(extract_text(browser.find_element_by_css_selector(
        '#ctl00_ContentPlaceHolder1_lblFile2'
    )))
    proposal_title = extract_text(browser.find_element_by_css_selector(
        '#ctl00_ContentPlaceHolder1_lblTitle2'
    ))
    proposal_type = extract_text(browser.find_element_by_css_selector(
        '#ctl00_ContentPlaceHolder1_lblIntroduced2'
    ))
    proposal_status = extract_text(browser.find_element_by_css_selector(
        '#ctl00_ContentPlaceHolder1_lblStatus2'
    ))
    introduction_date = parse_date(extract_text(
        browser.find_element_by_css_selector(
            '#ctl00_ContentPlaceHolder1_lblIntroduced2'
        )
    ))
    
    db_proposal = db.Proposal(file_number, proposal_title)
    db_proposal.status = proposal_status
    db_proposal.proposal_type = proposal_type
    db_proposal.introduction_date = introduction_date
    
    db.session.add(db_proposal) 
    db.session.flush()
        # TODO probably should refactor this out a t least

    return db_proposal

def scrape_vote_page(browser):
    """
    Assuming the browser is on a page containing a grid of votes, scrapes
    the vote data to populate the database.
    """
    # Get the contents of the table
    headers, rows = extract_grid_cells(browser, VOTING_GRID_ID)
    # Do a quick check to ensure our assumption about the headers is correct
    assert headers[:6] == [
        u'File #', 
        u'Action Date', 
        u'Title', 
        u'Action Details', 
        u'Meeting Details',
        u'Tally',
    ]

    # Go through the supervisors and add them to the DB if they are missing
    supervisors = headers[6:]
    legislator_objects = {}

    db.session.flush()

    # Pull values from each row and use them to populate the database
    second_browser = webdriver.Firefox()
    try:
        for row in rows: 
            file_number = int(extract_text(row['File #']))
            action_date = parse_date(extract_text(row['Action Date']))

            # Find the proposal in the DB, or, if it isn't there,
            # create a record for it by scraping the info page about that 
            # proposal.
            db_proposal = find_proposal(file_number) or scrape_proposal_page(
                second_browser,
                extract_href(row['File #'])
            )

            db_vote_event = db.VoteEvent(db_proposal, action_date)
            db.session.add(db_vote_event)
            db.session.flush()

            for name in supervisors:
                vote_cast = extract_text(row[name])
                if vote_cast in ('Aye', 'No'):
                    db.session.add(db.Vote(
                        record_supervisor(name),
                        db_proposal,
                        vote_cast == 'Aye'
                    ))
    finally:
        second_browser.close()

def scrape_vote_listing(browser):
    """
    Starting from the first page and working to the last page, scrapes all
    votes from a multi-page grid and populates the database.
    """
    page_number = 1
    while select_grid_page(browser, VOTING_GRID_ID, page_number):
        scrape_vote_page(browser)
        db.session.flush()
        page_number += 1

def scrape_vote_years(year_range):
    """
    Opens the votes page and scrapes the votes for all years in the given range.
    Populates the database and commits the transaction
    """
    browser = webdriver.Firefox()
    try:
        # Navigate to the Board of Supervisors page
        browser.get('https://sfgov.legistar.com/MainBody.aspx')

        # Click the votes tab
        people_tab = browser.find_element_by_partial_link_text('Votes')
        people_tab.click()

        # Scrape each year of votes
        for year in year_range:
            if not select_dropdown_option(
                    browser,
                    'ctl00_ContentPlaceHolder1_lstTimePeriodVoting_Input',
                    str(year)
                ):
                raise Exception("Year not found in options.")

            scrape_vote_listing(browser)

        db.session.commit()
    except:
        db.session.rollback()
        raise
    finally:
        browser.close()

#
# Browser/DOM helpers
#
def select_dropdown_option(browser, selectbox_id, option_text):
    """
    Interacts with a Telerik select-style control to select the option
    identified by the option_text.
    """
    # Click the select box so Telerik will dynamically populate it
    selectbox = browser.find_element_by_id(
        selectbox_id
    )
    selectbox.click()

    # Wait for the dropdown to appear
    time.sleep(PATIENCE)

    # Get the option items
    dropdown_id = selectbox_id.replace('Input', 'DropDown') #TODO hacky! 
    dropdown = browser.find_element_by_id(dropdown_id)
    option_items = dropdown.find_elements_by_css_selector(
        'div:nth-child(1) > ul:nth-child(1) > li'
    )

    # Find the requested option
    for li in option_items:
        if option_text == extract_text(li):
            li.click()
            time.sleep(PATIENCE)
            return True
    
    return False

def select_grid_page(browser, grid_id, page_number):
    """
    Selects the specified page number for a grid view in the browser,
    if that page number is visible as an option. Returns True on success,
    false on failure.
    """
    table = browser.find_element_by_id(grid_id)
    page_spans = table.find_elements_by_css_selector(
        'thead > tr.rgPager > td > table > tbody > tr > td  a > span'
    )

    number_string = str(page_number)
    for index, span in enumerate(page_spans):
        span_text = extract_text(span)
        if number_string == span_text:
            span.click()
            time.sleep(PATIENCE) # TODO is this needed?
            return True
        elif span_text == '...' and index == len(page_spans) - 1:
            # We're on the last option and still haven't found ours,
            # so it could be on the next "page" of pages
            # (which we have to explicitly request with another page load)
            span.click()
            time.sleep(PATIENCE)
            return select_grid_page(browser, grid_id, page_number)
    
    return False
    

def extract_grid_cells(browser, grid_id):
    """
    Given the ID of a legistar table, returns a list of dictionaries
    for each row mapping column headers to td elements.
    """
    table = browser.find_element_by_id(grid_id)
    
    header_cells = table.find_elements_by_css_selector(
        'thead:nth-child(2) > tr:nth-child(2) > th'
    )
    headers = [extract_text(cell) for cell in header_cells]

    tbody = table.find_element_by_css_selector('tbody:nth-child(4)')
    rows = tbody.find_elements_by_tag_name('tr')

    result_rows = []
    for row in rows:
        cells = {}
        td_elements = row.find_elements_by_tag_name('td')
        for header, cell in zip(headers, td_elements):
            cells[header] = cell

        result_rows.append(cells)

    return (headers, result_rows)

def extract_text(element):
    """
    Returns the text from an element in a nice, readable form with whitespace 
    trimmed and non-breaking spaces turned into regular spaces.
    """
    return element.get_attribute('textContent').replace(u'\xa0', ' ').strip()

def extract_href(element):
    """
    Returns the href property of the first link found in the element's tree.
    """
    return element.find_element_by_tag_name('a').get_attribute('href')

def parse_date(date_text):
    """
    Converts a date string in the American mm/dd/yyyy format to a Python
    date object.
    """
    month, day, year = [int(field) for field in date_text.split('/')]
    return date(year, month, day)

#
# DB helpers
#
def record_supervisor(name):
    """ 
    Queries for the given supervisor, creates a record for them in the 
    database if they aren't there already, and returns a Legislator
    object.
    """
    legislator = db.session.query(db.Legislator).filter_by(name=name).first()
    if not legislator:
        legislator = db.Legislator(name)
        db.session.add(legislator)
        db.session.flush()

    return legislator

def find_proposal(file_number):
    """
    Queries the database for a proposal based on its file number. Returns
    either the proposal model or None if it is not recorded.
    """
    return (db.session.query(db.Proposal)
        .filter_by(file_number=file_number)
        .first()
    )

#
# Main script
#
parser = argparse.ArgumentParser(description=
    '''
    Populate a database with several years of voting records from the San 
    Francisco board of supervisors.
    '''
)
parser.add_argument('first_year', metavar='first year', type=int)
parser.add_argument('last_year', metavar='last year', type=int)
args = parser.parse_args()

scrape_vote_years(range(args.first_year, args.last_year + 1))
    
