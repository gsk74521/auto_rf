*** Settings ***
Documentation    Test suite generated from session quick containing 1 test case for web automation.
Library         Browser
Test Tags       automated    generated    web

*** Test Cases ***
Example 快速验收
    [Documentation]    Test case that navigates to page.
    New Persistent Context    F:/github/auto_robot/demo/quick_profile    chromium    headless=True    url=https://example.com/
    Evaluate JavaScript    ${None}    () => { localStorage.clear(); sessionStorage.clear(); }
    Go To    https://example.com/
    Get Title
    Get Text    css=p >> nth=0
    Get Element Count    css=a
    Get Url
    [Teardown]    Close Browser    
