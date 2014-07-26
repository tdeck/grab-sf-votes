from selenium import webdriver
import time

browser = webdriver.Firefox()

browser.get('https://sfgov.legistar.com/MainBody.aspx')

# Click the people tab
"""
people_tab = browser.find_element_by_xpath(
   '//*[@id="ctl00_ContentPlaceHolder1_tabBottom"]/div/ul/li[2]/a/span/span/span'
)
"""
people_tab = browser.find_element_by_partial_link_text('People')
people_tab.click()

# Get a list of links to each supervisor's details
main_table = browser.find_element_by_id(
    'ctl00_ContentPlaceHolder1_gridPeople_ctl00'
)
supervisor_link_cells = main_table.find_elements_by_class_name('rgSorted')[1:]
supervisor_links = [
    cell.find_element_by_tag_name('a') 
        for cell in supervisor_link_cells
]

supervisor_links[0].click()

# Click the votes tab
votes_tab = browser.find_element_by_partial_link_text('Votes')
votes_tab.click()

# Get the excel export
export_dropdown = browser.find_element_by_link_text('Export')
export_dropdown.click()

time.sleep(1)

export_button = browser.find_element_by_link_text('Export to Excel')
export_button.click()

"""
# Select drop-down box to grab all votes in a given year
year_select = browser.find_element_by_id("ctl00_ContentPlaceHolder1_lstTimePeriodVoting_Input")

https://sfgov.legistar.com/DepartmentDetail.aspx?ID=7374&GUID=978C35A3-7173-49E6-8FAA-8EA34A7D4160&Mode=MainBody#
element.click()
"""
