import json

from playwright.sync_api import Page, sync_playwright

from logger import logger


def extract_entertainment_news(page: Page) -> list[dict[str, str]]:
    """Extract top 5 entertainment news articles."""
    entertainment_news: list[dict[str, str]] = []

    logger.info("Navigating to entertainment section...")
    page.goto("https://ekantipur.com/entertainment", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    # Scroll to trigger lazy loading
    page.evaluate("window.scrollBy(0, 500)")
    page.wait_for_timeout(1000)

    # Get category
    category_el = page.query_selector("div.category-name a")
    category_text = category_el.text_content() if category_el else None
    category = category_text.strip() if category_text else ""
    if not category:
        logger.warning("Category not found on page")

    heading_links = page.query_selector_all("div.category-description h2 a")
    logger.info(f"Found {len(heading_links)} article headings")

    count = 0
    processed_titles = set()

    for heading_link in heading_links:
        if count >= 5:
            break

        try:
            # Get title
            title = heading_link.text_content()
            if title:
                title = title.strip()

            if not title or title in processed_titles:
                continue
            processed_titles.add(title)

            # Get image
            image_url = (
                heading_link.evaluate(
                    """
                el => {
                    const parent = el.closest('.category-description')?.parentElement;
                    if (parent) {
                        const img = parent.querySelector('.category-image img');
                        return img?.src || img?.dataset?.src || null;
                    }
                    return null;
                }
            """
                )
                or ""
            )

            # Get author
            author = heading_link.evaluate(
                """
                el => {
                    const parent = el.closest('.category-description');
                    if (parent) {
                        const author = parent.querySelector('.author-name a');
                        return author ? author.textContent.trim() : null;
                    }
                    return null;
                }
            """
            )

            if not image_url:
                logger.warning(f"Missing image for: {title[:30]}...")
            if not author:
                logger.warning(f"Missing author for: {title[:30]}...")

            entertainment_news.append(
                {
                    "title": title,
                    "image_url": image_url,
                    "category": category,
                    "author": author,
                }
            )
            count += 1
            logger.info(f"Extracted: {title[:50]}...")

        except Exception as e:
            logger.error(f"Error extracting article: {e}")
            continue

    return entertainment_news


def extract_cartoon_of_the_day(page: Page) -> dict[str, str]:
    """Extract the latest cartoon of the day."""
    cartoon_data: dict[str, str] = {
        "title": "",
        "image_url": "",
        "author": "",
    }

    logger.info("Navigating to cartoon section...")
    page.goto("https://ekantipur.com/cartoon", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    # Scroll to trigger lazy loading
    page.evaluate("window.scrollBy(0, 500)")
    page.wait_for_timeout(1000)

    try:
        cartoon_wrapper = page.query_selector(".cartoon-wrapper")

        if cartoon_wrapper:
            # Get image
            cartoon_data["image_url"] = cartoon_wrapper.evaluate(
                """
                    el => {
                        const img = el.querySelector('img');
                        return img?.src || img?.dataset?.src || null;
                    }
                """
            )

            # Get title from cartoon-header first
            header_element = cartoon_wrapper.query_selector(".cartoon-header h4")
            if header_element and (text := header_element.text_content()):
                cartoon_data["title"] = text.strip()

            # Get author from <p> tags
            # (two patterns: "कार्टुनिष्ट: Name" or "Title - Author")
            author_data = cartoon_wrapper.evaluate(
                """
                el => {
                    const ps = el.querySelectorAll('p');
                    for (const p of ps) {
                        const text = p.textContent || '';
                        if (text.includes('कार्टुनिष्ट')) {
                            return { author: text.replace('कार्टुनिष्ट:', '').trim() };
                        }
                        if (text.includes(' - ')) {
                            const parts = text.split(' - ');
                            return {
                                title: parts.slice(0, -1).join(' - ').trim(),
                                author: parts.pop().trim()
                            };
                        }
                    }
                    return null;
                }
            """
            )
            if author_data:
                cartoon_data["author"] = author_data.get("author", "")
                if not cartoon_data["title"] and author_data.get("title"):
                    cartoon_data["title"] = author_data.get("title", "")

            if not cartoon_data["title"]:
                logger.warning("Missing cartoon title")
            if not cartoon_data["image_url"]:
                logger.warning("Missing cartoon image")
            if not cartoon_data["author"]:
                logger.warning("Missing cartoon author")

            title_preview = cartoon_data["title"][:50] or "N/A"
            logger.info(f"Extracted cartoon: {title_preview}...")

    except Exception as e:
        logger.error(f"Error extracting cartoon: {e}")

    return cartoon_data


def main():
    """Run the scraper and save results to output.json."""
    logger.info("=" * 50)
    logger.info("       Ekantipur Web Scraper")
    logger.info("=" * 50)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Chrome/120.0.0.0",
        )

        page = context.new_page()
        page.set_default_timeout(30000)

        try:
            logger.info("Task 1: Extracting Entertainment News")
            entertainment_news = extract_entertainment_news(page)
            logger.info(f"Extracted {len(entertainment_news)} articles")

            logger.info("Task 2: Extracting Cartoon of the Day")
            cartoon_data = extract_cartoon_of_the_day(page)
            logger.info("Extracted cartoon data")

            output_data = {
                "entertainment_news": entertainment_news,
                "cartoon_of_the_day": cartoon_data,
            }

            with open("output.json", "w", encoding="utf-8") as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

            logger.info("=" * 50)
            logger.info("Scraping completed successfully")
            logger.info("Data saved to output.json")
            logger.info("=" * 50)

        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            raise

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
