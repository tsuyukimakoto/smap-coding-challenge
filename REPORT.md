## Assumption

Usually I check the specifications, but the following is assumed this time.

- There are less than 10,000 files under one directory.
- `user_data.csv`'s id is number.
- Consumption is information with the first decimal place.
- No data with the same datetime is generated for the same data_id. If it occurs, the one that reaches first will be positive.
- Does not import consumption data in a differential (incremental).

## Developing Environment

- OS: macOS 10.14.6
- Python: 3.6.8
- SQLite3: library:2.6.0 engine:'3.22.0'
- Django: 1.11.23

## Coding Style

- Basically follow pycodestyle
  - The difference is defined in setup.cfg
- Write multiple import each line
  - This makes diff readablity better

## Project Structure

Basically follow the book 'Two scoops of Django (1.11)'.

### Project directory

- Project wide settings goes to config
  - I rename dashboard/dashboard to dashboard/config

### Applicaiton Directory

- Group first-party modules into packages called challenges. In the end, there was only one application, then.
  - As for Account data, it was good to divide the application, but 
  I' rather wanted to load it simultaneously with the import command, I did'nt do it.

- What I didn't do
  - Assembling settings from environment variables. Preparation for using the same image in multiple environments.

### Template Directory

- The templates directory is the same level as the application package directory.
  - For libraries that are reused in other projects, templates in the application directory are better.
  - The purpose is to make it easier for people who develop html to find.

- base.html
  - Django developers expected base.html to be in each application name directory, so I created base.html. Each html file in the directory inherits the application base.html.
  - The top-level template file is usually named base.html, so I renamed layout.html to base.html.

### requirements.txt

- Rather than using a single requirements.txt file, I have created files for each usage in the requirements directory.
  - The purpose is to separate libraries that are only needed for development

### Makefile

- Use as a convenient macro for development. Not for provisioning purposes.

### Temporary directory

- Collect temporary files in a directory named `.tmp`. It is easy to re-initialize.
  - Put sqlite data file there, too.

## Model

### Account

- I named it Account because it is a contract unit, not a person
- The id of the `user_data.csv` is `data_id`. The input from the outside is not suitable as a surrogate key.
- `data_id` is annoying whether it is a string or a number. I maked it number.

### Consumption

- Consumption is information with the first decimal place.
  - Since SQLite3 does not have a decimal data type, it is multiplied by 10 and stored as an integer.
  - To be precise, if the decimal type is defined, it falls back to the NUMERIC type and is finally retained as the real type.
- When I use ExtractMonth for datetime type, the operation is slow, so I denormalize to keep the year, month and day values.
  - datetime and ExtractMonth: about 5 second
  - year and month: about 0.2 second
- To avoid the following problems, I created a factory method to the Custom Manager.
  - \_\_setattr\_\_ is always called during model generation
  - Denormalization should be done in one place, or I will forget to implement it someday.
  - I can't use save signal or create manager because I want to use bulk_create.

## Problem

- I tried to import data in parallel using multiprocessing for each data_id, but I gave up because SQLite locked.
- I tried to make only csv reading and model list generation in parallel, but it was not as fast as I thought.
  - When I stopped using strptime, it was worth the time to try it because it became linearly faster up to several times the number of cores.
