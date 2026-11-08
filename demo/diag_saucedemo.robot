*** Settings ***
Library    Browser

*** Test Cases ***
Diag Saucedemo
    New Persistent Context    F:/github/auto_robot/demo/diag_profile3    chromium    headless=True    url=https://www.saucedemo.com/
    ${u1}=    Get Url
    Log To Console    URL1: ${u1}
    Fill Text    id=user-name    standard_user
    Fill Text    id=password    secret_sauce
    Click    id=login-button
    ${u2}=    Get Url
    Log To Console    URL2: ${u2}
    ${title}=    Get Text    css=.title
    Log To Console    TITLE: ${title}
    ${items}=    Get Element Count    css=.inventory_item
    Log To Console    ITEMS: ${items}
    ${cnt}=    Get Element Count    id=add-to-cart-sauce-labs-backpack
    Log To Console    ADDCART_COUNT: ${cnt}
    Close Browser
