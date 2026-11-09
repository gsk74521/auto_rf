*** Settings ***
Documentation    Test suite generated from session quick containing 1 test case for web automation.
Library         Browser
Test Tags       automated    generated    web

*** Test Cases ***
Example acceptance
    [Documentation]    Test case that navigates to page.
    New Persistent Context    ${OUTPUTDIR}${/}browser-profile    chromium    headless=True    url=https://example.com/
    Evaluate JavaScript    ${None}    () => { localStorage.clear(); sessionStorage.clear(); }
    Go To    https://example.com/
    Get Title    ==    Example Domain
    Get Element Count    css=a    >=    1
    Get Url    ==    https://example.com/
    [Teardown]    Close Browser    
