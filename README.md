# Redwood
This is the code for my personal web site located at
[www.henriktreadup.com](https://www.henriktreadup.com). It is a Python/Flask
application that is hosted on Heroku and uses S3 for file storage.

You will not be able to use this code without making some
modifications yourself. For example all the hardcoded S3 bucket names
would have to be changed.

## Environment Variables
To use this application you need to set the following environment variables.

These environment variables are needed for handling authentication.

    IDENTITY_JWT_SECRET=<secret for signing jwt>
    USERNAME=<username>
    PASSWORD_HASH=<password hash>
    PASSWORD_SALT=<random salt>

The following is pseudo code for how the password hash is calculated.

    PASSWORD_HASH = tohex(sha256(salt + password))

These environment variables are needed for accessing S3.

    AWS_ACCESS_KEY_ID=<aws access key id>
    AWS_SECRET_ACCESS_KEY=<aws secret access key>

## Testing
To run the unit tests locally use the following command.

    python test_redwood.py

This project uses a simple CI/CD pipeline on drone.io to deploy the
project to Heroku.
[![Build Status](https://cloud.drone.io/api/badges/treadup/redwood/status.svg)](https://cloud.drone.io/treadup/redwood)

## Git Hooks
There are some git hooks in the .githooks folder in this project. To
run these hooks change git to use the .githooks folder as the path to
the git hooks folder. This is done using the following command.

    git config core.hooksPath .githooks
