"""
Scrape CMU syllabus-registry from Canvas and make a JSON file of links to the Canvas syllabi for every course.
"""

import time
import json

from selenium.webdriver.common.keys import Keys
from selenium.webdriver import Firefox

# Which terms to get syllabi for
TERMS_TO_USE = ["S20", "F19", "M19", "N19"]

# Number of sections' individual syllabi to include (ideally should be 1 if all syllabi are uploaded properly)
LIMIT_SECTIONS_PER_COURSE_PER_TERM = 3

syllabi = {} # Format: {courseId: (name, [(term, section, url)... ])}

with Firefox() as driver:

    # Allow the user to log in and open the syllabus registry home page
    driver.get("https://login.cmu.edu")
    input("Please log in and press ENTER to proceed")
    time.sleep(3)

    driver.get("https://canvas.cmu.edu/courses/sis_course_id:syllabus-registry")
    time.sleep(5)

    # Get all of the links to each department (prefix) course detail page
    department_links = [x.get_attribute("href") for x in driver.find_elements_by_tag_name("a")]
    department_links = [l for l in department_links if (l is not None and "https://canvas.cmu.edu/courses/sis_course_id:syllabus-registry-" in str(l))]

    # Separate the department links by term
    links_by_term = {}
    for term in TERMS_TO_USE:
        links_by_term[term] = []

    for link in department_links:
        term = link.split("-")[-2]
        if term in links_by_term:
            links_by_term[term].append(link)

    # For every term and department, go to the department/term page and find all the syllabus links on the page
    for term in TERMS_TO_USE:
        for department_link in links_by_term[term]:

            driver.get(department_link)
            time.sleep(3)

            section = driver.find_elements_by_xpath("//div[@aria-label='Available Syllabi']")
            # If invalid page with no syllabi
            if len(section) == 0:
                continue

            syllabus_links = section[0].find_elements_by_tag_name("a")
            syllabus_links = [l for l in syllabus_links if l.get_attribute("class") == "ig-title title item_link"]

            # Track the number of sections for a given course that have been saved already
            visited = {}

            # Parse the syllabus link and add it to the syllabus list
            for link in syllabus_links:
                try:
                    title = link.text
                    url = link.get_attribute("href")
                    courseID = int(title[0:5])
                    section = title.split(":")[0]

                    name = title
                    if ":" in title:
                        # Get rid of the section / course #, keep the rest
                        name = ":".join(title.split(":")[1:]).strip()

                    if courseID in visited:
                        if visited[courseID] >= LIMIT_SECTIONS_PER_COURSE_PER_TERM:
                            continue
                        else:
                            visited[courseID] += 1
                    else:
                        visited[courseID] = 1

                    if courseID not in syllabi:
                        syllabi[courseID] = (name, [])

                    syllabi[courseID][1].append((term, section, url))

                    print("Successfully saved {}".format(title))

                except:
                    try:
                        print("Failed to save {} - {}".format(link, link.text))
                    except:
                        # Should never get here unless something seriously went wrong
                        print("Failed to save {}".format(link))


# Save the list to a JSON file
with open("syllabi.json", "w+") as file:
    json.dump(syllabi, file)
