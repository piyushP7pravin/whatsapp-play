'''
HOW TO USE

'''

import asyncio
import sys
from pyppeteer import launch

websites = {'whatsapp': 'https://web.whatsapp.com/'}
test_target = 'alexandre'


async def main():
    __patch_pyppeteer()
    browser = await config_browser(is_headless=False, is_auto_close=False)
    page_one, _ = await config_pages(browser)
    await page_one.bringToFront()
    await open_website(page_one, websites['whatsapp'])
    await open_new_chat(page_one)
    await type_in_search_bar(page_one, test_target)
    contact_list = await search_contacts_filtered(page_one, test_target)
    group_list = await search_groups_filtered(page_one, test_target)
    target_list = await get_target_list(contact_list, group_list)
    await print_target_list(page_one, test_target, contact_list, group_list, target_list)
    final_target_index = await choose_filtered_target(target_list)
    await navigate_to_target(page_one, target_list, final_target_index)
    await send_message(page_one, 'oi, tudo bem?')
    # await navigate_to_message_area(page_one, websites['whatsapp'])


# https://github.com/miyakogi/pyppeteer/pull/160
# HACK: We need this until this update is accepted.
# BUG:(Pyppeteer) The communication with Chromium are disconnected after 20s.
def __patch_pyppeteer():
    from typing import Any
    from pyppeteer import connection, launcher
    import websockets.client

    class PatchedConnection(connection.Connection):  # type: ignore
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self._ws = websockets.client.connect(
                self._url,
                loop=self._loop,
                max_size=None,  # type: ignore
                ping_interval=None,  # type: ignore
                ping_timeout=None,  # type: ignore
            )

    connection.Connection = PatchedConnection
    launcher.Connection = PatchedConnection


def __get_whatsapp_selectors_dict(target=None):
    whatsapp_selectors_dict = {
        'new_chat_button': '#side > header div[role="button"] span[data-icon="chat"]',
        'search_contact_input': '#app > div > div span > div > span > div div > label > input',
        'contact_list_filtered': '#app > div > div span > div > span > div div > div div > div div > span > span[title][dir]',
        'group_list_filtered': '#app > div > div span > div > span > div div > div div > div div > span[title][dir]',
        'message_area': '#main > footer div.selectable-text[contenteditable]'
    }
    return whatsapp_selectors_dict


async def config_browser(is_headless, is_auto_close):
    return await launch(headless=is_headless, autoClose=is_auto_close)


async def config_pages(browser):
    await browser.newPage()
    pages = await browser.pages()
    page_one = pages[0]
    page_two = pages[1]
    return page_one, page_two


async def open_website(page, website):
    await page.goto(website, waitUntil='networkidle2', timeout=0)


def return_if_wrong_url(page,url_to_check):
    if not page.url == url_to_check: 
        print("Wrong URL!")
        return


# Clicks in 'New Chat' to open your contact list
async def open_new_chat(page):  
    return_if_wrong_url(page, websites['whatsapp'])
    whatsapp_selectors_dict = __get_whatsapp_selectors_dict()
    await page.waitForSelector(
        whatsapp_selectors_dict['new_chat_button'],
        visible=True,
        timeout=0
    )
    await page.click(whatsapp_selectors_dict['new_chat_button'])


async def type_in_search_bar(page, target):
    return_if_wrong_url(page, websites['whatsapp'])
    whatsapp_selectors_dict = __get_whatsapp_selectors_dict(target)
    print(f'Looking for: {target}')
    await page.waitForSelector(
        whatsapp_selectors_dict['search_contact_input'],
        visible=True
    )
    await page.type(whatsapp_selectors_dict['search_contact_input'], target)
    await page.waitFor(3000)


async def search_contacts_filtered(page, target):
    return_if_wrong_url(page, websites['whatsapp'])
    whatsapp_selectors_dict = __get_whatsapp_selectors_dict(target)
    contact_list = list()
    try:
        await page.waitForSelector(
            whatsapp_selectors_dict['contact_list_filtered'],
            visible=True
        )

        contact_list = await page.querySelectorAll(
            whatsapp_selectors_dict['contact_list_filtered']
        )
    except:
        print(f'No contact named by "{target}"!')
    return contact_list


async def search_groups_filtered(page, target):
    return_if_wrong_url(page, websites['whatsapp'])
    whatsapp_selectors_dict = __get_whatsapp_selectors_dict(target)
    group_list = list()

    try:
        await page.waitForSelector(
            whatsapp_selectors_dict['group_list_filtered'],
            visible=True
        )

        group_list = await page.querySelectorAll(
            whatsapp_selectors_dict['group_list_filtered']
        )
    except:
        print(f'No group named by "{target}"!')
    return group_list


async def get_target_list(contact_list, group_list):
    return contact_list + group_list


async def print_target_list(page, target, contact_list, group_list, target_list):
    return_if_wrong_url(page, websites['whatsapp'])
    whatsapp_selectors_dict = __get_whatsapp_selectors_dict(target)
    try:
        for i in range(len(target_list)):
            if i < len(contact_list):
                if i == 0 and len(contact_list) > 0:
                    print("Contacts found:")
                contact_title = await page.evaluate(
                    f'document.querySelectorAll("{whatsapp_selectors_dict["contact_list_filtered"]}")[{i}].getAttribute("title")'
                )
                if (
                    contact_title.lower().find(target.lower()) != -1
                    and len(contact_list) > 0
                ):
                    print(f'{i}: {contact_title}')
                else:
                    target_list.pop(i)
            elif i >= len(contact_list):
                if i == len(contact_list) and len(group_list) > 0:
                    print("Groups found:")
                group_title = await page.evaluate(
                    f'document.querySelectorAll("{whatsapp_selectors_dict["group_list_filtered"]}")[{i - len(contact_list)}].getAttribute("title")'
                )
                if (group_title.lower().find(target.lower()) != -1):
                    print(f'{i- len(contact_list)}: {group_title}')
                else:
                    target_list.pop(i)
    except Exception as e:
        print(str(e))


async def choose_filtered_target(target_list):
    final_target_index = int(
        input('Enter the number of the target you wish to choose: '))
    return final_target_index


async def navigate_to_target(page, target_list, final_target_index):
    return_if_wrong_url(page, websites['whatsapp'])
    await target_list[final_target_index].click()


async def wait_for_message_area(page):
    return_if_wrong_url(page, websites['whatsapp'])
    whatsapp_selectors_dict = __get_whatsapp_selectors_dict()
    await page.waitForSelector(whatsapp_selectors_dict['wpp_message_area'])


async def send_message(page, message):
    return_if_wrong_url(page, websites['whatsapp'])
    whatsapp_selectors_dict = __get_whatsapp_selectors_dict()
    await page.type(
        whatsapp_selectors_dict['message_area'],
        message
    )
    await page.keyboard.press('Enter')


asyncio.get_event_loop().run_until_complete(main())

'''
# FIX: 
# To load websites faster
async def intercept(request, page_one, page_two):
    await page_one.setRequestInterception(True)
    await page_two.setRequestInterception(True)
    if any(request.resourceType == _ for _ in ('stylesheet', 'image', 'font', 'media')):
        await request.abort()
    else:
        await request.continue_()
    page.on('request', lambda req: asyncio.ensure_future(intercept(req)))
'''
