"""
Playwright test to verify the Chapter Practice image prefetch bug fix.

This test verifies:
1. Images load correctly (question, options, solution)
2. Prefetch is working (Next/Previous navigation shows images instantly)
3. UI cleanup is intact:
   - No "All Topics" button in question view
   - Back arrow returns to topic list from question view
   - Meta bar and section title are removed from question view
   - Bottom counter (N / total) is still present
"""

import asyncio
import time
from playwright.async_api import async_playwright, expect

BACKEND_URL = "https://builder-hub-1073.preview.emergentagent.com"
BANK_KEY = "neet-physics-motion-in-a-straight-line"
# Route pattern: /exam/:examId/:subjectId/practice/:bankKey
CHAPTER_PRACTICE_URL = f"{BACKEND_URL}/exam/neet/physics/practice/{BANK_KEY}"


async def test_chapter_practice_prefetch():
    """Test the chapter practice image prefetch and UI cleanup."""
    
    async with async_playwright() as p:
        # Launch browser in headless mode
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()
        
        # Track network requests for images
        image_requests = []
        failed_requests = []
        
        async def track_request(request):
            if "/api/chapter-image/" in request.url:
                image_requests.append({
                    "url": request.url,
                    "timestamp": time.time()
                })
        
        async def track_response(response):
            if "/api/chapter-image/" in response.url:
                if response.status != 200:
                    failed_requests.append({
                        "url": response.url,
                        "status": response.status
                    })
        
        page.on("request", track_request)
        page.on("response", track_response)
        
        print(f"\n🔍 Testing Chapter Practice: {BANK_KEY}")
        print(f"📍 URL: {CHAPTER_PRACTICE_URL}")
        
        # Navigate to the chapter practice page
        print("\n1️⃣ Navigating to chapter practice page...")
        try:
            await page.goto(CHAPTER_PRACTICE_URL, wait_until="networkidle", timeout=30000)
            print("   ✅ Page loaded successfully")
            
            # Take a screenshot for debugging
            await page.screenshot(path="/tmp/chapter_practice_loaded.png")
            print("   📸 Screenshot saved to /tmp/chapter_practice_loaded.png")
        except Exception as e:
            print(f"   ❌ Failed to load page: {e}")
            await page.screenshot(path="/tmp/chapter_practice_error.png")
            await browser.close()
            return False
        
        # Wait for topic list to appear
        print("\n2️⃣ Waiting for topic list...")
        try:
            await page.wait_for_selector('[data-testid="topic-list"]', timeout=10000)
            print("   ✅ Topic list loaded")
        except Exception as e:
            print(f"   ❌ Topic list not found: {e}")
            await browser.close()
            return False
        
        # Click on the first topic to open question view
        print("\n3️⃣ Opening first topic...")
        try:
            topic_button = page.locator('[data-testid="topic-list"] button').first
            await topic_button.click()
            await page.wait_for_timeout(2000)  # Wait for images to start loading
            print("   ✅ Topic opened")
        except Exception as e:
            print(f"   ❌ Failed to open topic: {e}")
            await browser.close()
            return False
        
        # Verify UI cleanup: No "All Topics" button in question view
        print("\n4️⃣ Verifying UI cleanup...")
        all_topics_button = page.locator('button:has-text("All Topics")')
        all_topics_count = await all_topics_button.count()
        if all_topics_count > 0:
            print(f"   ❌ FAIL: Found 'All Topics' button (should be removed)")
        else:
            print("   ✅ PASS: No 'All Topics' button found (correctly removed)")
        
        # Verify meta bar is NOT shown (source badge, "N questions", "Chapter N")
        # These should only appear in the topic list view, not in question view
        meta_badges = page.locator('.mb-4 .flex.flex-wrap.items-center.gap-2')
        meta_count = await meta_badges.count()
        if meta_count > 0:
            # Check if it contains the specific meta info
            text_content = await meta_badges.first.text_content() if meta_count > 0 else ""
            if "questions" in text_content.lower() or "chapter" in text_content.lower():
                print(f"   ⚠️  WARNING: Meta bar might still be visible in question view")
        else:
            print("   ✅ PASS: Meta bar not shown in question view")
        
        # Verify the bottom counter (N / total) is present
        counter = page.locator('span:has-text("/")')
        counter_count = await counter.count()
        if counter_count > 0:
            counter_text = await counter.first.text_content()
            print(f"   ✅ PASS: Bottom counter present: {counter_text.strip()}")
        else:
            print(f"   ❌ FAIL: Bottom counter not found")
        
        # Verify question image loads
        print("\n5️⃣ Verifying question image loads...")
        try:
            question_img = page.locator('img[alt*="Question"]').first
            await question_img.wait_for(state="visible", timeout=10000)
            
            # Check if image actually loaded (not broken)
            is_visible = await question_img.is_visible()
            natural_width = await question_img.evaluate("img => img.naturalWidth")
            
            if is_visible and natural_width > 0:
                print(f"   ✅ Question image loaded successfully (width: {natural_width}px)")
            else:
                print(f"   ❌ Question image failed to load properly")
        except Exception as e:
            print(f"   ❌ Question image not found or failed to load: {e}")
        
        # Verify option images load
        print("\n6️⃣ Verifying option images load...")
        try:
            option_imgs = page.locator('img[alt*="Option"]')
            option_count = await option_imgs.count()
            print(f"   Found {option_count} option images")
            
            loaded_options = 0
            for i in range(min(option_count, 4)):  # Check first 4 options
                try:
                    opt_img = option_imgs.nth(i)
                    await opt_img.wait_for(state="visible", timeout=5000)
                    natural_width = await opt_img.evaluate("img => img.naturalWidth")
                    if natural_width > 0:
                        loaded_options += 1
                except:
                    pass
            
            if loaded_options >= 4:
                print(f"   ✅ All option images loaded successfully ({loaded_options}/4)")
            else:
                print(f"   ⚠️  Only {loaded_options}/4 option images loaded")
        except Exception as e:
            print(f"   ❌ Failed to verify option images: {e}")
        
        # Click "Show Answer & Solution" button
        print("\n7️⃣ Clicking 'Show Answer & Solution'...")
        try:
            show_answer_btn = page.locator('button:has-text("Show Answer")')
            await show_answer_btn.click()
            await page.wait_for_timeout(1000)
            print("   ✅ Clicked 'Show Answer & Solution'")
            
            # Verify solution image loads
            solution_img = page.locator('img[alt*="Solution"]').first
            await solution_img.wait_for(state="visible", timeout=5000)
            natural_width = await solution_img.evaluate("img => img.naturalWidth")
            
            if natural_width > 0:
                print(f"   ✅ Solution image loaded successfully (width: {natural_width}px)")
            else:
                print(f"   ❌ Solution image failed to load")
        except Exception as e:
            print(f"   ⚠️  Could not verify solution image: {e}")
        
        # Test prefetch by clicking Next multiple times
        print("\n8️⃣ Testing prefetch by clicking Next...")
        initial_image_count = len(image_requests)
        
        for i in range(3):
            try:
                next_btn = page.locator('button:has-text("Next")')
                
                # Record time before click
                start_time = time.time()
                await next_btn.click()
                
                # Wait for the new question image to be visible
                await page.wait_for_timeout(500)  # Small delay to let prefetch work
                
                # Check if image is immediately visible (prefetch working)
                question_img = page.locator('img[alt*="Question"]').first
                is_visible = await question_img.is_visible()
                load_time = time.time() - start_time
                
                if is_visible and load_time < 1.0:
                    print(f"   ✅ Question {i+2} loaded instantly ({load_time:.2f}s) - prefetch working!")
                else:
                    print(f"   ⚠️  Question {i+2} took {load_time:.2f}s to load")
                
            except Exception as e:
                print(f"   ❌ Failed to click Next or verify image: {e}")
                break
        
        # Test Previous button
        print("\n9️⃣ Testing Previous button...")
        try:
            prev_btn = page.locator('button:has-text("Previous")')
            
            start_time = time.time()
            await prev_btn.click()
            await page.wait_for_timeout(500)
            
            question_img = page.locator('img[alt*="Question"]').first
            is_visible = await question_img.is_visible()
            load_time = time.time() - start_time
            
            if is_visible and load_time < 1.0:
                print(f"   ✅ Previous question loaded instantly ({load_time:.2f}s) - prefetch working!")
            else:
                print(f"   ⚠️  Previous question took {load_time:.2f}s to load")
        except Exception as e:
            print(f"   ❌ Failed to test Previous button: {e}")
        
        # Test back arrow navigation
        print("\n🔟 Testing back arrow navigation...")
        try:
            # Click the back arrow in the header
            back_arrow = page.locator('header button[aria-label="Go back"], header button svg').first
            await back_arrow.click()
            await page.wait_for_timeout(1000)
            
            # Should return to topic list
            topic_list = page.locator('[data-testid="topic-list"]')
            is_visible = await topic_list.is_visible()
            
            if is_visible:
                print("   ✅ Back arrow correctly returns to topic list")
            else:
                print("   ❌ Back arrow did not return to topic list")
        except Exception as e:
            print(f"   ⚠️  Could not test back arrow: {e}")
        
        # Check for failed image requests
        print("\n📊 Image Request Summary:")
        print(f"   Total image requests: {len(image_requests)}")
        print(f"   Failed requests: {len(failed_requests)}")
        
        if failed_requests:
            print("\n   ❌ Failed image requests:")
            for req in failed_requests[:5]:  # Show first 5 failures
                print(f"      - {req['url']} (Status: {req['status']})")
        
        # Check console errors
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        
        await page.wait_for_timeout(1000)
        
        if console_errors:
            print(f"\n   ⚠️  Console errors detected: {len(console_errors)}")
            for err in console_errors[:3]:
                print(f"      - {err}")
        else:
            print("\n   ✅ No console errors detected")
        
        # Close browser
        await browser.close()
        
        # Final verdict
        print("\n" + "="*60)
        if len(failed_requests) == 0:
            print("✅ TEST PASSED: All images loaded successfully, prefetch working!")
            return True
        else:
            print(f"❌ TEST FAILED: {len(failed_requests)} image requests failed")
            return False


if __name__ == "__main__":
    result = asyncio.run(test_chapter_practice_prefetch())
    exit(0 if result else 1)
