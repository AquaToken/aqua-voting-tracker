<div id="top"></div>


<!-- PROJECT SHIELDS -->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/AquaToken/aqua-voting-tracker">
    <img src="https://aqua.network/assets/img/header-logo.svg" alt="Logo" width="250" height="80">
  </a>

<h3 align="center">Aquarius Voting Tracker</h3>

  <p align="center">
    Aquarius protocol is governed by DAO voting with AQUA tokens. Vote and participate in discussions to shape the future of Aquarius.
    <br />
    <br />
    <a href="https://github.com/AquaToken/aqua-voting-tracker/issues">Report Bug</a>
    ·
    <a href="https://vote.aqua.network/">Request Feature</a>
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
        <li><a href="#development-server">Development server</a></li>
      </ul>
    </li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

[![Aquarius voting tool Screen Shot][product-screenshot]](https://vote.aqua.network/)


#### What is Aquarius voting?
Aquarius allows the community of AQUA holders to signal where liquidity is needed through a voting process. This introduces an additional liquidity management layer for the whole Stellar network.

AQUA token holders decide on the market pairs where liquidity is needed most, and also define the size of market maker rewards for each pair.

#### How does voting work?
The voting happens on-chain so the votes can be independently validated by any user. Aquarius provides an interface visualising the votes and current rewards in various markets, as well as a separate dashboard where AQUA holders can vote. Voting works with most Stellar wallets including hardware wallets such as Ledger.

After each round of voting, Aquarius aggregates the individual votes of all Stellar users. Based on the results it defines a list of markets where the incentives should be activated.


<p align="right">(<a href="#top">back to top</a>)</p>



### Built With

* [Python](https://python.org/)
* [Django](https://www.djangoproject.com/)
* [Django REST framework](https://www.django-rest-framework.org/)
* [Celery](https://docs.celeryq.dev/en/stable/getting-started/introduction.html)
* [Stellar SDK](https://pypi.org/project/stellar-sdk/)

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- GETTING STARTED -->

## Getting Started

### Prerequisites
Project is using postgresql as a database, so it's the only requirement.

### Development server
Project built using django framework, so setup is similar to generic django project.

#### Clone project
`git clone git@github.com:AquaToken/aqua-voting-tracker.git`

#### Create environment & install requirements
`pipenv sync --dev`

#### Setup environment variable
```
echo 'export DATABASE_URL="postgres://username@password:localhost/aqua_voting_tracker"' > .env
```

#### Migrate database
`pipenv run python manage.py migrate --noinput`

#### Run server
`pipenv run python manage.py runserver 0.0.0.0:8000`

#### Run celery beater (background scheduler)
`pipenv run celery -A aqua_voting_tracker.taskapp beat`

#### Run celery worker (background worker)
`pipenv run celery -A aqua_voting_tracker.taskapp worker`

#### Done
That's it. Admin panel as well as api will be available at 8000 port: `http://localhost:8000/admin/login/`


<p align="right">(<a href="#top">back to top</a>)</p>


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

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Email: [hello@aqua.network](mailto:hello@aqua.network)
Telegram chat: [@aquarius_HOME](https://t.me/aquarius_HOME)
Telegram news: [@aqua_token](https://t.me/aqua_token)
Twitter: [@aqua_token](https://twitter.com/aqua_token)
GitHub: [@AquaToken](https://github.com/AquaToken)
Discord: [@Aquarius](https://discord.gg/sgzFscHp4C)
Reddit: [@AquariusAqua](https://www.reddit.com/r/AquariusAqua/)
Medium: [@aquarius-aqua](https://medium.com/aquarius-aqua)

Project Link: [https://github.com/AquaToken/aqua-voting-tracker](https://github.com/AquaToken/aqua-voting-tracker)

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/AquaToken/aqua-voting-tracker.svg?style=for-the-badge
[contributors-url]: https://github.com/AquaToken/aqua-voting-tracker/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/AquaToken/aqua-voting-tracker.svg?style=for-the-badge
[forks-url]: https://github.com/AquaToken/aqua-voting-tracker/network/members
[stars-shield]: https://img.shields.io/github/stars/AquaToken/aqua-voting-tracker.svg?style=for-the-badge
[stars-url]: https://github.com/AquaToken/aqua-voting-tracker/stargazers
[issues-shield]: https://img.shields.io/github/issues/AquaToken/aqua-voting-tracker.svg?style=for-the-badge
[issues-url]: https://github.com/AquaToken/aqua-voting-tracker/issues
[license-shield]: https://img.shields.io/github/license/AquaToken/aqua-voting-tracker.svg?style=for-the-badge
[license-url]: https://github.com/AquaToken/aqua-voting-tracker/blob/master/LICENSE.txt
[product-screenshot]: images/screenshot.png
