# A utility that configures S3 and Route53 to host a static website on your domain.

## Features:  
* Creates a bucket and a route53 record that points to it
* Takes care of creating new hosted zone if needed
* Supports [Root Domain Website Hosting](http://aws.typepad.com/aws/2012/12/root-domain-website-hosting-for-amazon-s3.html)

## Requirements:
Any system with python and pip (Tested on Ubuntu 13.10 Desktop).    

The boto credentials have to be [discoverable](http://boto.readthedocs.org/en/latest/getting_started.html) via environment variables, ~/.boto file or IAM role.

## Installation:
```
sudo pip install boto
wget https://raw.github.com/flypunk/s3host/master/s3host -O s3host
chmod +x s3host
```
## Usage:

`./s3host domainname`

Feedback and pull requests are welcome! 
