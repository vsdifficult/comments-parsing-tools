import json
import time
from typing import Iterator, Dict, Optional
from pathlib import Path
from datetime import datetime 
from logging import getLogger

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from http.client import IncompleteRead 

from comment_parser.storage.comments_storage import CommentsStorage 
from comment_parser.storage.models import Comment 

try:
    import undetected_chromedriver as uc
    _USE_UC = True
except Exception:
    _USE_UC = False

class SeleniumYouTubeParser:
    def __init__(self, headless: bool = False, driver_path: Optional[str] = None, slow_mode: bool = True):
        self._storage = CommentsStorage()
        self._driver = self._init_driver()
        self._logger = getLogger("SeleniumYouTubeParser") 
        self.headless = headless
        self.driver_path = driver_path
        self.slow_mode = slow_mode

    def _create_driver(self):
        global _USE_UC
        driver = None
        
        if _USE_UC:
            for attempt in range(2):
                try:
                    options = uc.ChromeOptions()
                    if self.headless:
                        options.add_argument("--headless=new")
                    options.add_argument("--no-sandbox")
                    options.add_argument("--disable-blink-features=AutomationControlled")
                    options.add_argument("--disable-dev-shm-usage")
                    options.add_argument("--lang=en-US")
                    
                    print(f"Attempting to create undetected_chromedriver ({attempt + 1}/2)...")
                    driver = uc.Chrome(options=options, use_subprocess=True)
                    print("✓ Successfully created undetected_chromedriver")
                    break
                except (IncompleteRead, Exception) as e:
                    print(f"✗ Undetected_chromedriver error: {e}")
                    if attempt < 1:
                        time.sleep(3)
                    else:
                        print("→ Switching to regular Selenium WebDriver")
                        driver = None
        
        if driver is None:
            try:
                print("Creating regular Chrome WebDriver...")
                options = Options()
                if self.headless:
                    options.add_argument("--headless=new")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument("--lang=en-US")
                options.add_argument("--disable-gpu")
                options.add_argument("--window-size=1920,1080")
                
                options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                
                driver = webdriver.Chrome(options=options)
                print("✓ Successfully created Chrome WebDriver")
            except Exception as e:
                print(f"✗ Critical error creating driver: {e}")
                raise e
        
        driver.set_window_size(1920, 1080)
        return driver 
    
    def _scroll_to_comments(self, driver):
        """Scrolls the page to the comments section"""
        print("Scrolling to comments section...")
        for i in range(5):
            driver.execute_script("window.scrollBy(0, 400);")
            time.sleep(0.3)

    def _debug_print_html(self, driver):
        """Debug function to print comment structure"""
        try:
            threads = driver.find_elements(By.CSS_SELECTOR, "ytd-comment-thread-renderer")
            if threads:
                print(f"\n=== DEBUG: First comment structure ===")
                html = threads[0].get_attribute('outerHTML')[:1000]
                print(html)
                print("=" * 50)
        except Exception as e:
            print(f"Debug error: {e}") 

    def stream_comments(self, video_url: str, max_comments: int = None, 
                        scroll_pause: float = 2.0, debug: bool = False) -> Iterator[Dict]:
            """Streaming comments: yield each found comment thread"""
            driver = self._create_driver()
            
            try:
                print(f"Opening URL: {video_url}")
                driver.get(video_url)
                time.sleep(4)
                
                self._scroll_to_comments(driver)
                
                print("Waiting for comments section to load...")
                try:
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-comments"))
                    )
                    print("✓ ytd-comments section found.")
                    time.sleep(3)
                except TimeoutException:
                    print("✗ Comments section not found.")
                    driver.quit()
                    return

                try:
                    disabled_msg = driver.find_element(By.CSS_SELECTOR, "ytd-message-renderer")
                    msg_text = disabled_msg.text.lower()
                    if "disabled" in msg_text or "отключен" in msg_text or "turned off" in msg_text:
                        print("✗ Comments are disabled for this video.")
                        driver.quit()
                        return
                except NoSuchElementException:
                    pass
                
                if debug:
                    self._debug_print_html(driver)
                
                last_height = driver.execute_script("return document.documentElement.scrollHeight")
                seen_ids = set()
                yielded = 0
                no_new_comments_count = 0
                scroll_count = 0
                
                selectors_to_try = [
                    ("ytd-comment-thread-renderer", "yt-attributed-string#content-text", "yt-formatted-string#author-text", "span#vote-count-middle"),
                    ("ytd-comment-thread-renderer", "#content-text", "#author-text span", "#vote-count-middle"),
                    ("ytd-comment-thread-renderer", "yt-formatted-string.ytd-comment-renderer", "#author-text", "#vote-count-middle"),
                ]
                
                while True:
                    scroll_count += 1
                    print(f"\n--- Scroll #{scroll_count} ---")
                    
                    driver.execute_script(
                        "window.scrollTo({top: document.documentElement.scrollHeight, behavior: 'smooth'});"
                    )
                    time.sleep(scroll_pause + (1.0 if self.slow_mode else 0.0))
                    
                    elems = driver.find_elements(By.CSS_SELECTOR, "ytd-comment-thread-renderer")
                    print(f"Found ytd-comment-thread-renderer elements: {len(elems)}")
                    
                    if debug and scroll_count == 1 and len(elems) > 0:
                        print("\n=== Checking selectors on first element ===")
                        test_elem = elems[0]
                        for i, (thread_sel, text_sel, author_sel, likes_sel) in enumerate(selectors_to_try):
                            print(f"\nVariant #{i+1}:")
                            try:
                                text_e = test_elem.find_element(By.CSS_SELECTOR, text_sel)
                                print(f"  ✓ Text found: {text_sel} -> '{text_e.text[:50]}...'")
                            except:
                                print(f"  ✗ Text NOT found: {text_sel}")
                            try:
                                author_e = test_elem.find_element(By.CSS_SELECTOR, author_sel)
                                print(f"  ✓ Author found: {author_sel} -> '{author_e.text}'")
                            except:
                                print(f"  ✗ Author NOT found: {author_sel}")
                        print("=" * 50)
                    
                    new_in_batch = 0
                    for e in elems:
                        comment_data = None
                        
                        for thread_sel, text_sel, author_sel, likes_sel in selectors_to_try:
                            try:
                                cid = e.get_attribute("id")
                                
                                text = ""
                                try:
                                    text_elem = e.find_element(By.CSS_SELECTOR, text_sel)
                                    text = text_elem.text.strip()
                                except NoSuchElementException:
                                    continue 

                                if not text:
                                    continue
                                
                                author = ""
                                try:
                                    author_elem = e.find_element(By.CSS_SELECTOR, author_sel)
                                    author = author_elem.text.strip()
                                except NoSuchElementException:
                                    pass
                                
                                time_text = ""
                                time_selectors = [
                                    "a.yt-simple-endpoint.style-scope.yt-formatted-string",
                                    "yt-formatted-string.published-time-text a",
                                    ".published-time-text a",
                                    "a#published-time-text",
                                ]
                                for time_sel in time_selectors:
                                    try:
                                        time_elem = e.find_element(By.CSS_SELECTOR, time_sel)
                                        time_text = time_elem.text.strip()
                                        if time_text:
                                            break
                                    except NoSuchElementException:
                                        continue
                                
                                likes = "0"
                                try:
                                    likes_elem = e.find_element(By.CSS_SELECTOR, likes_sel)
                                    likes_text = likes_elem.text.strip()
                                    likes = likes_text if likes_text else "0"
                                except NoSuchElementException:
                                    pass
                                
                                comment_data = {
                                    "source": "youtube",
                                    "url": video_url,
                                    "id": cid or f"comment_{yielded}",
                                    "content": text,
                                    "likes": int(likes.replace(",", "").replace(".", "") if likes else "0"),
                                    "date": time_text,
                                    "author": author,
                                }
                                break  
                                
                            except Exception as ex:
                                if debug:
                                    print(f"Error with selector set: {ex}")
                                continue
                        
                        if comment_data and comment_data["id"] not in seen_ids:
                            seen_ids.add(comment_data["id"])
                            yielded += 1
                            new_in_batch += 1
                            yield comment_data
                            
                            if max_comments and yielded >= max_comments:
                                print(f"✓ Limit reached: {max_comments} comments")
                                driver.quit()
                                return
                    
                    print(f"New comments in this scroll: {new_in_batch}")
                    print(f"Total collected: {yielded}")
                    
                    new_height = driver.execute_script("return document.documentElement.scrollHeight")
                    
                    if new_in_batch == 0:
                        no_new_comments_count += 1
                    else:
                        no_new_comments_count = 0
                    
                    if new_height == last_height or no_new_comments_count >= 3:
                        print(f"\n✓ Parsing completed. Collected {yielded} comments.")
                        break
                    
                    last_height = new_height

            finally:
                try:
                    driver.quit()
                except:
                    pass 

    def save_to_json(self, video_url: str, output_file: str, 
                     max_comments: int = None, scroll_pause: float = 2.0, debug: bool = False) -> int:
        """
        Parses comments and saves through storage
        
        Returns:
            int: number of saved comments
        """
        print(f"\n{'='*60}")
        print(f"Starting comment parsing")
        print(f"URL: {video_url}")
        print(f"{'='*60}\n")
        
        comment_count = 0
        comments = []  
        for comment in self.stream_comments(video_url, max_comments, scroll_pause, debug):
            comments.append(Comment(**comment)) 
            comment_count += 1
            if comment_count % 10 == 0:
                print(f"📝 Comments collected: {comment_count}")
        
        print(f"\n{'='*60}")
        print(f"✓ Saved {comment_count} comments to {output_file}")
        print(f"{'='*60}\n")
        return comment_count

    def translate_comment(self, comment: str, target_language: str = "ru") -> str:
        """
        Translates comment to specified language using Google Translate.
        
        Args:
            comment (str): Comment text to translate.
            target_language (str): Target language code (default "ru" for Russian).
        
        Returns:
            str: Translated comment text.
        """
        from googletrans import Translator, LANGUAGES
        
        translator = Translator()
        try:
            detected_language = translator.detect(comment).lang
            print(f"Detected comment language: {LANGUAGES.get(detected_language, detected_language)}")
            
            if detected_language != target_language:
                translated = translator.translate(comment, dest=target_language)
                print(f"Translated from {LANGUAGES.get(detected_language)} to {LANGUAGES.get(target_language)}")
                return translated.text
            else:
                print("Comment is already in target language.")
                return comment
        except Exception as e:
            print(f"Translation error: {e}")
            return comment  

    def stream_comments_with_translation(self, video_url: str, max_comments: int = None, 
                                         scroll_pause: float = 2.0, debug: bool = False, 
                                         target_language: str = "ru") -> Iterator[Dict]:
        """Streaming comments with translation: yield each found comment thread"""
        driver = self._create_driver()
        
        try:
            print(f"Opening URL: {video_url}")
            driver.get(video_url)
            time.sleep(4)
            
            self._scroll_to_comments(driver)
            
            print("Waiting for comments section to load...")
            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-comments"))
                )
                print("✓ ytd-comments section found.")
                time.sleep(3)
            except TimeoutException:
                print("✗ Comments section not found.")
                driver.quit()
                return

            try:
                disabled_msg = driver.find_element(By.CSS_SELECTOR, "ytd-message-renderer")
                msg_text = disabled_msg.text.lower()
                if "disabled" in msg_text or "отключен" in msg_text or "turned off" in msg_text:
                    print("✗ Comments are disabled for this video.")
                    driver.quit()
                    return
            except NoSuchElementException:
                pass
            
            if debug:
                self._debug_print_html(driver)
            
            last_height = driver.execute_script("return document.documentElement.scrollHeight")
            seen_ids = set()
            yielded = 0
            no_new_comments_count = 0
            scroll_count = 0
            
            selectors_to_try = [
                ("ytd-comment-thread-renderer", "yt-attributed-string#content-text", "yt-formatted-string#author-text", "span#vote-count-middle"),
                ("ytd-comment-thread-renderer", "#content-text", "#author-text span", "#vote-count-middle"),
                ("ytd-comment-thread-renderer", "yt-formatted-string.ytd-comment-renderer", "#author-text", "#vote-count-middle"),
            ]
            
            while True:
                scroll_count += 1
                print(f"\n--- Scroll #{scroll_count} ---")
                
                driver.execute_script(
                    "window.scrollTo({top: document.documentElement.scrollHeight, behavior: 'smooth'});"
                )
                time.sleep(scroll_pause + (1.0 if self.slow_mode else 0.0))
                
                elems = driver.find_elements(By.CSS_SELECTOR, "ytd-comment-thread-renderer")
                print(f"Found ytd-comment-thread-renderer elements: {len(elems)}")
                
                if debug and scroll_count == 1 and len(elems) > 0:
                    print("\n=== Checking selectors on first element ===")
                    test_elem = elems[0]
                    for i, (thread_sel, text_sel, author_sel, likes_sel) in enumerate(selectors_to_try):
                        print(f"\nVariant #{i+1}:")
                        try:
                            text_e = test_elem.find_element(By.CSS_SELECTOR, text_sel)
                            print(f"  ✓ Text found: {text_sel} -> '{text_e.text[:50]}...'")
                        except:
                            print(f"  ✗ Text NOT found: {text_sel}")
                        try:
                            author_e = test_elem.find_element(By.CSS_SELECTOR, author_sel)
                            print(f"  ✓ Author found: {author_sel} -> '{author_e.text}'")
                        except:
                            print(f"  ✗ Author NOT found: {author_sel}")
                    print("=" * 50)
                
                new_in_batch = 0
                for e in elems:
                    comment_data = None
                    
                    for thread_sel, text_sel, author_sel, likes_sel in selectors_to_try:
                        try:
                            cid = e.get_attribute("id")
                            
                            text = ""
                            try:
                                text_elem = e.find_element(By.CSS_SELECTOR, text_sel)
                                text = text_elem.text.strip()
                            except NoSuchElementException:
                                continue 

                            if not text:
                                continue
                            
                            author = ""
                            try:
                                author_elem = e.find_element(By.CSS_SELECTOR, author_sel)
                                author = author_elem.text.strip()
                            except NoSuchElementException:
                                pass
                            
                            time_text = ""
                            time_selectors = [
                                "a.yt-simple-endpoint.style-scope.yt-formatted-string",
                                "yt-formatted-string.published-time-text a",
                                ".published-time-text a",
                                "a#published-time-text",
                            ]
                            for time_sel in time_selectors:
                                try:
                                    time_elem = e.find_element(By.CSS_SELECTOR, time_sel)
                                    time_text = time_elem.text.strip()
                                    if time_text:
                                        break
                                except NoSuchElementException:
                                    continue
                            
                            likes = "0"
                            try:
                                likes_elem = e.find_element(By.CSS_SELECTOR, likes_sel)
                                likes_text = likes_elem.text.strip()
                                likes = likes_text if likes_text else "0"
                            except NoSuchElementException:
                                pass
                            
                            comment_data = {
                                "source": "youtube",
                                "url": video_url,
                                "id": cid or f"comment_{yielded}",
                                "content": text,
                                "likes": int(likes.replace(",", "").replace(".", "") if likes else "0"),
                                "date": time_text,
                                "author": author,
                            }
                            break  
                            
                        except Exception as ex:
                            if debug:
                                print(f"Error with selector set: {ex}")
                            continue
                    
                    if comment_data and comment_data["id"] not in seen_ids:
                        seen_ids.add(comment_data["id"])
                        yielded += 1
                        new_in_batch += 1
                        
                        comment_data["content"] = self.translate_comment(comment_data["content"], target_language)
                        
                        yield comment_data
                        
                        if max_comments and yielded >= max_comments:
                            print(f"✓ Limit reached: {max_comments} comments")
                            driver.quit()
                            return
                
                print(f"New comments in this scroll: {new_in_batch}")
                print(f"Total collected: {yielded}")
                
                new_height = driver.execute_script("return document.documentElement.scrollHeight")
                
                if new_in_batch == 0:
                    no_new_comments_count += 1
                else:
                    no_new_comments_count = 0
                
                if new_height == last_height or no_new_comments_count >= 3:
                    print(f"\n✓ Parsing completed. Collected {yielded} comments.")
                    break
                
                last_height = new_height

        finally:
            try:
                driver.quit()
            except:
                pass 

    def save_to_json_with_translation(self, video_url: str, output_file: str, 
                                       max_comments: int = None, scroll_pause: float = 2.0, 
                                       debug: bool = False, target_language: str = "ru") -> int:
        """
        Parses comments and saves through storage with translation to Russian
        
        Returns:
            int: number of saved comments
        """
        print(f"\n{'='*60}")
        print(f"Starting comment parsing with translation to {target_language}")
        print(f"URL: {video_url}")
        print(f"{'='*60}\n")
        
        comment_count = 0
        comments = [] 
        for comment in self.stream_comments_with_translation(video_url, max_comments, scroll_pause, debug, target_language):
            comments.append(Comment(**comment)) 
            comment_count += 1
            if comment_count % 10 == 0:
                print(f"📝 Comments collected: {comment_count}")
                
        print(f"\n{'='*60}")
        print(f"✓ Saved {comment_count} comments to {output_file}")
        print(f"{'='*60}\n")
        return comment_count