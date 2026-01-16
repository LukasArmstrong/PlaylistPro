<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a name="readme-top"></a>
<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
<!--
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
-->
[![Issues][issues-shield]][issues-url]
[![GPL License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/LukasArmstrong/Youtube-Playlist-Organizer">
    <img src="Images/PlaylistPro_Logo.png" alt="Logo" width=auto height="80">
  </a>

<h3 align="center">PlaylistPro</h3>

  <p align="center">
    Simple web app that sorts youtube watchlater by duration and assigned priority.
    <br />
    <!--
    <a href="https://github.com/LukasArmstrong/Youtube-Playlist-Organizer"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/LukasArmstrong/Youtube-Playlist-Organizer">View Demo</a>
    ·
    -->
    <a href="https://github.com/LukasArmstrong/Youtube-Playlist-Organizer/issues">Report Bug</a>
    ·
    <a href="https://github.com/LukasArmstrong/Youtube-Playlist-Organizer/issues">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#quick-start">Quick Start</a></li>
        <li><a href="#database-configuration">Database Configuration</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#project-structure">Project Structure</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

<!-- [![Product Name Screen Shot][product-screenshot]](https://example.com) -->

This started because I wanted to sort my watch later list on youtube by duration with some key exceptions for priority, some videos being in a series, some creators release order mattering, and one-off videos being follow up to longer videos. After I accomplished this goal and refactored the code a bit, I decided to keep enhancing the project. There are lots of little things I would like to add to make this a power user tool. However, unless something changes with the Youtube API quota limit, I doubt very many people will be able to use this project in its entirety. I would consider this project in its infancy still, but others are welcome to fork or make suggestions for changes.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

* [![Python][Python]][Python-url]
* [![Flask][Flask]][Flask-url]
* [![SQLAlchemy][SQLAlchemy]][SQLAlchemy-url]
* [![React][React]][React-url]
* [![YoutubeAPI][YoutubeAPI]][YoutubeAPI]
* [![MariaDB][MariaDB]][MariaDB-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started


### Prerequisites

* Python 3.8+
  - Download the [latest version](https://www.python.org/downloads/)
* pip
  - Download and follow [documentation](https://pip.pypa.io/en/stable/installation/#get-pip-py)
  - Make sure pip is up to date:
    ```sh
    pip install --upgrade pip
    ```
* YouTube API Credentials
  - Go to [Google's Cloud Console](https://console.cloud.google.com/)
  - Create a project and enable the YouTube Data API v3
  - Create OAuth 2.0 Client IDs under APIs & Services > Credentials


### Quick Start

Get up and running in minutes with SQLite (no database setup required):

1. **Clone the repo**
   ```sh
   git clone https://github.com/LukasArmstrong/PlaylistPro.git
   cd PlaylistPro
   ```

2. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```

3. **Set up YouTube API credentials**

   Create a `.env` file or export environment variables:
   ```sh
   export CLIENT_ID="your-client-id"
   export CLIENT_SECRET="your-client-secret"
   export PROJECT_ID="your-project-id"
   export AUTH_URI="https://accounts.google.com/o/oauth2/auth"
   export TOKEN_URI="https://oauth2.googleapis.com/token"
   export AUTH_PROVIDER="https://www.googleapis.com/oauth2/v1/certs"
   export REDIRECT_URIS="http://localhost:5000"
   export YOUTUBE_PLAYLIST_ID="your-playlist-id"
   export IDRIS_PROJECT_ID="1"
   export INTERNAL_FLOW_PORT="8080"
   export HOST_IP="0.0.0.0"
   export HOST_PORT="5000"
   ```

4. **Run the application**
   ```sh
   python3 YoutubeWebserver.py
   ```

   The app will automatically create a SQLite database (`playlistpro.db`) on first run.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


### Database Configuration

PlaylistPro supports multiple database backends via SQLAlchemy. The app automatically detects your environment:

| Environment | Database | Configuration |
|-------------|----------|---------------|
| Development | SQLite | Automatic (no setup needed) |
| Production | MariaDB/MySQL | Set `DATABASE_URL` or `ENVIRONMENT=production` |

#### Option 1: SQLite (Default)
No configuration needed. The app creates `playlistpro.db` automatically.

#### Option 2: Explicit DATABASE_URL
Set the `DATABASE_URL` environment variable:
```sh
# MariaDB/MySQL
export DATABASE_URL="mysql+pymysql://user:password@localhost:3306/playlistpro"

# PostgreSQL (also supported)
export DATABASE_URL="postgresql://user:password@localhost:5432/playlistpro"
```

#### Option 3: Production Mode with MariaDB Environment Variables
Set `ENVIRONMENT=production` and the app will use your existing MariaDB environment variables:
```sh
export ENVIRONMENT="production"
export DATABASE_SERVER_IP="localhost"
export DATABASE_PORT="3306"
export DATABASE_USER="your_user"
export DATABASE_PASSWORD="your_password"
export DATABASE="playlistpro"
```

#### Docker Compose Example
```yaml
version: '3.8'
services:
  playlistpro:
    build: .
    environment:
      - DATABASE_URL=mysql+pymysql://user:password@mariadb:3306/playlistpro
      # ... other env vars
    depends_on:
      - mariadb

  mariadb:
    image: mariadb:latest
    environment:
      - MYSQL_ROOT_PASSWORD=rootpassword
      - MYSQL_DATABASE=playlistpro
      - MYSQL_USER=user
      - MYSQL_PASSWORD=password
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



## Usage

1. **Get an OAuth token** (first time only):
   ```
   http://<YOUR_HOST_IP>:<PORT>/renew
   ```

2. **Sort your playlist**:
   Navigate to the home page and click the sort button, or visit:
   ```
   http://<YOUR_HOST_IP>:<PORT>/
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



## Project Structure

```
PlaylistPro/
├── YoutubeWebserver.py      # Flask application entry point
├── pywertube/               # Core library package
│   ├── __init__.py          # Package exports
│   ├── db.py                # SQLAlchemy database instance
│   ├── models.py            # Database models (8 tables)
│   ├── database.py          # Database helper functions
│   ├── youtube_api.py       # YouTube API interactions
│   ├── sorting.py           # Playlist sorting algorithms
│   ├── quota.py             # API quota tracking
│   ├── utils.py             # Utility functions
│   └── logging_config.py    # Logging configuration
├── templates/               # Flask HTML templates
├── static/                  # Static assets (CSS, JS)
└── requirements.txt         # Python dependencies
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

- [x] Add Getting Started Section to README
- [x] Add usage section to README
- [x] Proper logging support
- [x] SQLAlchemy ORM integration
- [x] SQLite support for easy development
- [X] Create frontend
    - [X] Login with Oauth
    - [X] button for sorting
    - [ ] GUI to add creator/keywords
    - [ ] GUI to delete creator/keywords
    - [ ] GUI to set/update creator/keyword priority
- [ ] Auto add videos to watchlater queue (hopefully in correct position)
     - [ ] Tool to scrape youtube subscriptions
- [ ] Smarter use of Quota limit data
- [ ] Track upload time to predict when creator videos should release
- [ ] Scrape youtube channels to collect data on publish times
- [ ] Look into token renewal process (see if automation can be performed)
- [ ] Make youtube playlist update function more efficient


See the [open issues](https://github.com/LukasArmstrong/Youtube-Playlist-Organizer/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the GPL License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Lukas Armstrong - PlaylistPro@LukasArmstrong.io

Project Link: [https://github.com/LukasArmstrong/PlaylistPro](https://github.com/LukasArmstrong/PlaylistPro)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/LukasArmstrong/pywerTube.svg?style=for-the-badge
[contributors-url]: https://github.com/LukasArmstrong/Youtube-Playlist-Organizer/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/LukasArmstrong/pywerTube.svg?style=for-the-badge
[forks-url]: https://github.com/LukasArmstrong/Youtube-Playlist-Organizer/network/members
[stars-shield]: https://img.shields.io/github/stars/LukasArmstrong/pywerTube.svg?style=for-the-badge
[stars-url]: https://github.com/LukasArmstrong/Youtube-Playlist-Organizer/stargazers
[issues-shield]: https://img.shields.io/github/issues/LukasArmstrong/pywerTube.svg?style=for-the-badge
[issues-url]: https://github.com/LukasArmstrong/Youtube-Playlist-Organizer/issues
[license-shield]: https://img.shields.io/github/license/LukasArmstrong/pywerTube.svg?style=for-the-badge
[license-url]: https://github.com/LukasArmstrong/Youtube-Playlist-Organizer/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/linkedin_username](https://www.linkedin.com/in/lukasarmstrong/
[product-screenshot]: images/screenshot.png

[Python]: https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[Flask]: https://img.shields.io/badge/flask-000000?style=for-the-badge&logo=flask&logoColor=white
[Flask-url]: https://flask.palletsprojects.com/en/3.0.x/
[SQLAlchemy]: https://img.shields.io/badge/sqlalchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white
[SQLAlchemy-url]: https://www.sqlalchemy.org/
[React]: https://img.shields.io/badge/-ReactJs-61DAFB?logo=react&logoColor=white&style=for-the-badge
[React-url]: https://react.dev/
[YoutubeAPI]: https://img.shields.io/badge/youtube_api-FF0000?style=for-the-badge&logo=youtube&logoColor=white
[YoutubAPI-url]: https://developers.google.com/youtube/v3
[MariaDB]: https://img.shields.io/badge/mariadb-003545?style=for-the-badge&logo=mariadb&logoColor=white
[MariaDB-url]: https://mariadb.com/
