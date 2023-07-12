from flask import Flask, render_template, request, url_for
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import time
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Set up the web driver in incognito mode
        chrome_options = Options()
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)

        # Load the website
        driver.get("https://clipdrop.co/stable-diffusion")
        driver.implicitly_wait(4)

        # Find the input field and enter user input
        user_input = request.form['prompt']
        input_field = driver.find_element(By.NAME, "prompt")
        input_field.send_keys(user_input)

        # Click the "Generate" button
        generate_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        generate_button.click()

        time.sleep(120)

        # Retrieve the specific div element with the generated content
        div_element = driver.find_element(By.XPATH, "//div[@class='flex items-center justify-center flex-1 w-full p-1 md:p-4 overflow-hidden']")

        # Use Beautiful Soup to parse the generated HTML and extract the image URLs
        soup = BeautifulSoup(div_element.get_attribute("innerHTML"), "html.parser")
        image_tags = soup.find_all("img")
        image_urls = [img["src"] for img in image_tags]

        # Generate watermarked images
        watermarked_images = []
        for i, url in enumerate(image_urls):
            # Open the image in a new tab
            driver.execute_script(f"window.open('{url}', '_blank')")
            driver.switch_to.window(driver.window_handles[-1])

            # Capture a screenshot of the image
            driver.save_screenshot(f"static/image_{i}.png")

            # Close the tab
            driver.close()

            # Switch back to the main tab
            driver.switch_to.window(driver.window_handles[0])

            # Open the input image
            image = Image.open(f"static/image_{i}.png")
            width, height = image.size

            # Create a transparent layer with the same size as the image
            watermark = Image.new('RGBA', (width, height), (0, 0, 0, 0))

            # Choose a font and font size for the watermark text
            font = ImageFont.truetype('arial.ttf', 26)

            # Create a drawing object
            draw = ImageDraw.Draw(watermark)

            # Calculate the position to place the watermark text
            text_width, text_height = draw.textsize('generated from clipdrop (non commercial)', font)
            x = (width - text_width) // 2
            y = (height - text_height) // 4

            # Draw the watermark text on the transparent layer
            draw.text((x, y), user_input, font=font)

            # Combine the original image with the watermark layer
            watermarked = Image.alpha_composite(image.convert('RGBA'), watermark)

            # Save the watermarked image
            watermarked.save(f"static/image_{i}.png")

            # Append the watermarked image to the list
            # watermarked_images.append(f"static/image_{i}.png")

        # Close the web driver
        driver.quit()

        # # get images from static folder
        image_folder = 'static'  # Path to the folder containing the images
        image_urls = []

        # Iterate over the files in the image folder
        for filename in os.listdir(image_folder):
            if filename.endswith('.jpg') or filename.endswith('.png'):
                image_path = os.path.join(image_folder, filename)
                image_urls.append(url_for('static', filename='/' + filename))

        return render_template('index.html', images=image_urls)
    else:
        return render_template('index.html', images=None)

if __name__ == '__main__':
    app.run(debug=True)
