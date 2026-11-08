*** Settings ***
Library    Browser

*** Test Cases ***
Clear State
    New Persistent Context    F:/github/auto_robot/demo/saucedemo_profile    chromium    headless=True    url=https://www.saucedemo.com/
    Evaluate JavaScript    ${None}    () => localStorage.clear()
    Log To Console    STATE_CLEARED
    Close Browser
