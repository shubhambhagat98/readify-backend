# Readify - An online book recommendation platform

![readify_thumb (4)](https://user-images.githubusercontent.com/53030762/202834255-ccd766c4-04e2-43a9-bae7-9cacfe7aec32.png)

## Project Proposal

Readify is a mobile-friendly book recommendation platform that offers engaging book recommendations. We provide detailed information and opportunities to learn more about over 50,000 best-selling books. Users can browse books, apply filters based on author, title, genre, and rating, as well as create booklists to save interesting books.

Depending on the books saved in your booklists, our machine learning algorithm will generate recommendations for you based on similar authors as well as by identifying keywords in titles and genres of those books.

Even before you create your booklists, we will generate initial recommendations for you depending on the top 3 genres you select while registering on our platform. This is done to handle cold-start.

## Tech Stack

- Prototyping - Figma
- Front-end - ReactJS, Material UI, CSS3. [Github repo](https://github.com/shubhambhagat98/Readify-frontend) for frontend code
- Back-end - Python (Flask)
- Database - MySQL
- Deployment - [Heroku](https://readify-app.herokuapp.com/)

## Demo

https://user-images.githubusercontent.com/53030762/202579925-9da5473c-9b26-45a4-b628-f5c908d8579f.mp4

## EDA and Data Preprocessing

- The dataset used for this project is the [Goodreads](https://zenodo.org/records/4265096#.YkJYHjfML0p) dataset.
- The dataset contains 10,000 books, each with various attributes such as title, author, average rating, ISBN, etc.
