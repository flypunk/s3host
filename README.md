# A utility that configures S3 and Route53 to host a static website on your domain.

## Features:  
* Supports [Root Domain Website Hosting](http://aws.typepad.com/aws/2012/12/root-domain-website-hosting-for-amazon-s3.html)!
* Creates a bucket and a route53 record that points to it
* Takes care of creating new hosted zone if needed
* Bucket names starting with www. are not supported due to HTTP 409 - A conflicting conditional operation is currently in progress

## Requirements:
Any system with python and pip (Tested on Ubuntu Desktop 13.10 and 14.04).

The boto credentials have to be [discoverable](http://boto.readthedocs.org/en/latest/getting_started.html) via environment variables, ~/.boto file or IAM role.

## Installation:
```
sudo pip install boto
wget https://raw.github.com/flypunk/s3host/master/s3host.py -O s3host.py
chmod +x s3host
```
## Usage:

`./s3host.py domainname`

Feedback and pull requests are welcome! 
