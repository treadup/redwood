# Publishing notes
First clone the existing notes.

    git clone git@github.com:treadup/notes.git

Then publish the notes to S3.

    aws s3 sync notes/ s3://redwood-notes
