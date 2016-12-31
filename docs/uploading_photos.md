# Uploading Photos
The photos are stored in the rainforestphotos bucket on S3. To upload
local photos to this bucket use the following aws cli command.

    aws s3 sync <source-folder> s3://rainforestphotos/<target-folder>/

Here is an example of the command.a

    aws s3 sync hawaii-2015/ s3://rainforestphotos/hawaii-2015/

The images can then be viewed using the following style of url.

    http://s3.amazonaws.com/rainforestphotos/hawaii-2015/hiking.jpg

