# Demo Script: Computer Vision Mode

Hi, I am Yusuf. This is EntityFlow's computer vision mode, built as a portfolio-ready showcase for image inspection and review.

First, I open the Vision page and upload a sample image. The frontend previews the image immediately so I can confirm I picked the correct file.

Next, I trigger visual inspection. The backend decodes the image, runs a lightweight OpenCV contour pipeline, stores the inspection run in PostgreSQL, and returns detected regions with bounding boxes.

After the results load, I can see the bounding boxes drawn directly on top of the image and a review panel on the right with confidence, coordinates, and current review status.

I can approve or reject a detection from either the overlay or the table. That action updates the review state in the UI and persists the change in the backend.

The goal is to show a clean multimodal workflow that is easy to understand in a portfolio: upload, inspect, review, and store the result.

If I want to test it locally, I run the backend on port 8000 and the frontend on port 5173, then open the Vision page in the browser and repeat the same steps.