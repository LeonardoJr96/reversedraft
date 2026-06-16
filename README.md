# ReverseDraft

> The complete competition management platform for leagues, tournaments, drafts, auctions, and championships.

ReverseDraft is an all-in-one platform designed to simplify the organization and management of competitive events. Whether you're running a sports league, esports tournament, fantasy competition, or community championship, ReverseDraft provides the tools needed to manage every stage of the competition lifecycle.

ReverseDraft is a comprehensive platform for managing competitions, leagues, drafts, and auctions. This repository contains the application core, including the `fifa_data` module, which processes and exposes detailed data for players, clubs, and leagues based on the SoFIFA structure.

## 🚀 Current Status: FIFA Data API

The project currently features a robust REST API built with **Django** and **Django REST Framework**, focused on providing statistical football data to power draft and auction systems.

### Key Features Implemented:
*   **Complete SoFIFA Modeling:** Support for Players, Clubs, Leagues, Stadiums, and detailed technical attributes.
*   **Advanced Filters (RQL):** Implementation of `dj-rql` for complex URL queries (e.g., filtering players by rating, age, and position in a single query).
*   **Roster Versioning:** Support for multiple rosters and attribute history (*Player Prime*).
*   **Trait and PlayStyle Management:** Complete mapping of special abilities and play styles.

## Features

### FIFA Data & Analytics (`fifa_data` module)
*   [x] Normalized data models for Players, Clubs, and Leagues.
*   [x] REST API for data consumption.
*   [x] Dynamic filter system via RQL.
*   [x] Mapping of technical, physical, and mental attributes.
*   [x] Bitmask support for Traits (official API style).

### In Development
*   [ ] Authentication System (JWT).
*   [ ] Draft Logic (Snake & Reverse).
*   [ ] Real-time Auction System.

### Team Management

* Create and manage teams
* Automatic team generation
* Team randomization
* Team balancing tools
* Player assignment and transfers

### Draft System

* Snake Draft
* Reverse Draft
* Custom Draft Rules
* Draft Order Management
* Real-time Draft Tracking

### Player Auctions

* Live Auction System
* Budget Management
* Bid Tracking
* Player Valuation
* Auction History

### Tournament Management

* Single Elimination
* Double Elimination
* Round Robin
* Group Stages
* Playoffs
* Knockout Brackets

### League Management

* Standings and Rankings
* Match Scheduling
* Fixtures Generation
* Points Configuration
* Tiebreaker Rules

### Randomization Tools

* Team Draws
* Player Draws
* Group Draws
* Match Draws
* Custom Randomization Rules

### Statistics & Analytics

* Team Statistics
* Player Statistics
* League Performance Metrics
* Historical Records
* Competition Reports

### Administration

* User Roles and Permissions
* Competition Settings
* Multi-League Support
* Audit Logs
* Event Management

## Use Cases

* Sports Championships
* Esports Tournaments
* Fantasy Leagues
* School Competitions
* Community Events
* Corporate Tournaments
* Amateur Leagues
* Professional Competitions

## Technology Stack

*   **Framework:** Django 6.0+
*   **API:** Django REST Framework (DRF)
*   **Query Language:** dj-rql (Resource Query Language)
*   **Database:** SQLite (Development) / PostgreSQL (Production)
*   **Real-Time Updates:** WebSockets (Planned)
* Deployment: Docker

## 🛠️ How to Run

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/LeonardoJr96/reversedraft.git
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run migrations:**
    ```bash
    python manage.py migrate
    ```
4.  **Start the server:**
    ```bash
    python manage.py runserver
    ```

## Roadmap

### Phase 1

* [ ] Authentication
* [ ] Team Management
* [ ] Player Management
* [ ] Competition Creation

### Phase 2

* [ ] Draft System
* [ ] Auction System
* [ ] Match Scheduling
* [ ] Standings

### Phase 3

* [ ] Bracket Generator
* [ ] Playoff System
* [ ] Statistics Dashboard
* [ ] Real-Time Updates

### Phase 4

* [ ] Public APIs
* [ ] Mobile Support
* [ ] Advanced Analytics
* [ ] Multi-Tenant Architecture

## Vision

ReverseDraft aims to become the operating system for competitive events, providing a unified platform where organizers can create, manage, automate, and analyze every aspect of a competition.

## Contributing

Contributions are welcome. Feel free to submit issues, feature requests, and pull requests.

## License

This project is licensed under the MIT License.

---

**ReverseDraft**
*From player auction to championship.*
