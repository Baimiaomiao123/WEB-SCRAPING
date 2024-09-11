######################################################################################
# Author: Miaomiao Bai                                                               #
# Time: 09/11/2024                                                                   #
# Version:1.0                                                                        #
# Description: This project is used for scraping keyboard information from Amazon    #
# Reference: https://www.youtube.com/watch?v=3gZecEHCgbs; Blogger: Servet Gulnaroglu #
######################################################################################


import asyncio
from playwright.async_api import async_playwright
import json


async def scrape_urls(page):
    await page.wait_for_selector(".a-size-mini.a-spacing-none.a-color-base.s-line-clamp-2 > a")
    urls = await page.eval_on_selector_all(
        ".a-size-mini.a-spacing-none.a-color-base.s-line-clamp-2 > a",
        "elements => elements.map(e => e.href)"
    )
    return urls


async def scrape_page_data(page, url):
    try:
        print(f'Scraping the url {url}')
        await page.goto(url, timeout=120000)
        await page.wait_for_selector("span#productTitle")  # Wait for the title to load
        title = await page.eval_on_selector("span#productTitle", "el => el.textContent")
        img_source = await page.eval_on_selector("div#imgTagWrapperId > img", "el => el.src")
        price = await page.eval_on_selector(".a-section.a-spacing-none.aok-align-center.aok-relative > .aok-offscreen",
                                            "el => el.textContent")
        rating = await page.eval_on_selector("span#acrPopover .a-size-base.a-color-base",
                                             "el => el.textContent")

        scraped_data = {
            "title": title.strip() if title else None,
            "url": url,
            "img_source": img_source,
            "price": price.strip() if price else None,
            "rating": rating.strip() if rating else None
        }
        return scraped_data
    except Exception as e:
        print(f'An error occurred scraping the url {url[:50]}...: {str(e)[:50]}...')
        return {}


async def main():
    scraped_data_file = 'scraped_data.json'
    scraped_data_all = []

    async with async_playwright() as pw:
        print('Connecting...')
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context()

        await context.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
        })

        for page_num in range(1, 3):
            page = await context.new_page()

            try:
                print(f'Navigating to page {page_num}...')
                await page.goto(f"https://www.amazon.com/s?k=keyboard&page={page_num}", timeout=120000)
                print(f'On page {page_num}')

                # Debug: Print page content
                page_content = await page.content()
                print(f'Page content:\n{page_content[:1000]}')  # Print first 1000 characters

                urls = await scrape_urls(page)
                print(f'Found URLs: {urls}')  # Debug: Print URLs found

                data = []

                for url in urls:
                    session_page = await context.new_page()
                    scraped_data = await scrape_page_data(session_page, url)
                    if scraped_data:
                        data.append(scraped_data)
                    await session_page.close()
                    print(scraped_data)

                print(data)
                scraped_data_all.extend(data)

            except Exception as e:
                print(f'Exception occurred: {str(e)[:50]}')
            finally:
                await page.close()

        await browser.close()

        with open(scraped_data_file, 'w') as file:
            print('Writing the file')
            json.dump(scraped_data_all, file, indent=4)


# Run the async main function
asyncio.run(main())
