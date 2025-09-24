# Beehive Placement Analyzer

This web application helps beekeepers in Poland find suitable locations for their beehives by analyzing parcel data against a set of predefined rules. The interactive map allows users to click on a location or search for a parcel ID to get a quick analysis.

## Features

*   **Interactive Map:** A map of Poland where users can explore and select locations.
*   **Parcel Analysis:** When a location is selected, the application checks for compliance with the following rules:
    *   10 m from residential, livestock, and farm buildings, gardens, yards, and busy public roads.
    *   50 m from highways and expressways.
    *   150 m from public facilities such as schools, clinics, nursing homes, and kindergartens.
    *   In ecological apiaries, 1 km from landfills and waste incinerators, and from busy roads, highways, and industrial centers.

## Getting Started

### Prerequisites

*   Python 3.x
*   Pip

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Set up the backend:**
    ```bash
    cd backend
    pip install -r requirements.txt
    python app.py
    ```

3.  **Open the frontend:**
    *   Open the `frontend/index.html` file in your web browser.

## Usage

1.  Navigate the map to your area of interest.
2.  Click on the map to select a parcel.
3.  The analysis results will be displayed on the screen.