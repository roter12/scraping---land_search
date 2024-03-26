## Setup

1. If you don’t have Python installed, [install it from here](https://www.python.org/downloads/).

2. Then, input the following command.

   ```bash
   python -m pip install beautifulsoup4 pandas selenium
   ```

## Run

   Input the following command.

   ```bash
   > python redfin.py
   ```

   Or
   ```bash
   > python redfin.py <zipcode> <minimum lot size> <maximum lot size>

   ```

   Or
   ```bash
   > python redfin.py <county> <state> <redfin code> <minimum lot size> <maximum lot size>

   ```

   You can see usage with the following command.
   ```bash
   > python redfin.py -h
   ```

   Results save as a CSV file in 'output' directory.