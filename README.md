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
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

<!-- [![Product Name Screen Shot][product-screenshot]](https://example.com) -->

This started because I wanted to sort my watch later list on youtube by duration with some key execepts to priority, some videos being in a series, some creators release order mattering, and one-off videos being follow up to longer videos. After I accomplish this goal and refactored the code a bit, I decided to keep enhancing the project. There are lots of little things I would like to add to make this a poweruser tool. However, unless something changes with the Youtube API quota limit, I doubt very many people will able to use this project in it's entirety. I would consider this project in its infancy still, but others are welcome to fork or make suggestions for changes.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

* [![Python][Python]][Python-url]
* [![Flask][Flask]][Flask-url]
* [![React][React]][React-url]
* [![YoutubeAPI][YoutubeAPI]][YoutubeAPI]
* [![MariaDB][MariaDB]][MariaDB-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started


### Prerequisites

* python
  - Download the [latest version](https://www.python.org/downloads/)
* pip
  - Download and follow [documentation](https://pip.pypa.io/en/stable/installation/#get-pip-py)
  - Make sure pip is up to date with the follow command:
    ```sh
    pip install --upgrade pip
    ```
* Client_secret.json file
  - Go to [Google's Cloud Console](https://console.cloud.google.com/)
  - Make a project and make sure youtube's v3 api is enabled.
  - Create OAuth 2.0 Client IDS under APIs & Services > Credentials.
* MariaDB Database
  - Please see schema under images.

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/LukasArmstrong/Youtube-Playlist-Organizer.git
   ```
2. Install required modules
   ```sh
   pip install -r requirements.txt
   ```
3. Place client_secret file in the directory
4. Update config.yaml
5. Start webserver
   ```sh
   python3 YoutubeWebServer.py
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>




## Usage

Admitedly, this where most of the work needs to be done. Currently, to run the sorting algorithm, you go to go to:
- ```url
  http://<YOUR_HOST_IP>/sort
  ```
However before the first sort, you'll need to get a token. This is done by:
- ```url
  http://<YOUR_HOST_IP>/renew
  ```
<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- ROADMAP -->
## Roadmap

- [x] Add Getting Started Section to README
- [x] Add usage section to README
- [x] Proper logging support
- [X] Create frontend
    - [X] Login with Oauth
    - [X] button for sorting
    - [ ] GUI to add creator/keywords
    - [ ] GUI to delete creator/keywords
    - [ ] GUI to set/update creator/keyword priority
- [ ] Auto add videos to watchlater queue. Hopefully in correct position
     - [ ] Tool to scrape youtube subscriptions 
- [ ] Smarter use of Quota limit data
- [ ] Track upload time to predict when creator videos should release
- [ ] Scrape youtube channels to collect data on publish times 
- [ ] Look into token renewal process. See if automation can be preformed  
- [ ] Make youtube play update function for efficient
  

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



<!-- ACKNOWLEDGMENTS 
## Acknowledgments

* []()
* []()
* []()
-->
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
[React]: https://img.shields.io/badge/-ReactJs-61DAFB?logo=react&logoColor=white&style=for-the-badge
[React-url]: https://react.dev/
[YoutubeAPI]: https://img.shields.io/badge/youtube_api-FF0000?style=for-the-badge&logo=youtube&logoColor=white
[YoutubAPI-url]: https://developers.google.com/youtube/v3
[MariaDB]: https://img.shields.io/badge/mariadb-003545?style=for-the-badge&logo=mariadb&logoColor=white
[MariaDB-url]: https://mariadb.com/
