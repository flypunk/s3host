#!/usr/bin/env python

import sys
import time
import argparse

import boto
from boto.s3.connection import ProtocolIndependentOrdinaryCallingFormat

# From http://docs.aws.amazon.com/general/latest/gr/rande.html#s3_region
us_east_1_website_hosted_zone = 'Z3AQBSTGFYJSTF'
us_east_1_website_endpoint = 's3-website-us-east-1.amazonaws.com.'

wrong_alias_error = ''' DNSServerError: 400 Bad Request
<?xml version="1.0"?>
<ErrorResponse xmlns="https://route53.amazonaws.com/doc/2012-02-29/"><Error><Type>Sender</Type><Code>InvalidChangeBatch</Code><Message>Tried to create an alias that targets YOUR_DOMAIN, type A in zone HOSTED_ZONE_ID, but the alias target name does not lie within the target zone</Message></Error><RequestId>1f140de0-6a51-11e3-8db4-2b67aa94f445</RequestId></ErrorResponse>
'''

def parse_args():
    description = 'Configure S3 and Route53 to host a static website on your domain'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('domain')
    return parser.parse_args()

def get_record_type(dns_name):
    '''
    Sorts the name it gets to 1 of 3 types: invalid, apex, normal.
    We split the trailing dot before making the decision.
    '''
    if dns_name.endswith('.'):
        dns_name = dns_name[:-1]
    levels = len(dns_name.split('.'))
    if levels  < 2:
        return False
    elif levels == 2:
        return 'apex'
    else:
        return 'cname'

def get_domain_apex(domain):
    '''Return the apex name, strip trailing dot for easier processing.'''
    if domain.endswith('.'):
        domain = domain[:-1]
    return '.'.join(domain.split('.')[-2:])

def create_bucket(s3_conn, domain, retries=10):
    '''Create a bucket, configure it as a website and make it publicly readable'''
    if domain.startswith('www.'):
        print('Sorry, bucket names starting with www. are not supported - exiting.')
        sys.exit(1)
    try:
        bucket = s3_conn.create_bucket(domain)
    except boto.exception.S3CreateError, e:
        print('Error while creating bucket %s: %s') % (domain, e)
        retries_left = retries
        for i in range(retries):
            print('Retrying...')
            time.sleep(1)
            try:
                bucket = s3_conn.create_bucket(domain)
            except:
                retries_left -= 1
            
        if not retries_left:
            print('Failed after %s retries' % retries)
            sys.exit(1)

    k = boto.s3.key.Key(bucket)
    k.key = 'index.html'
    k.set_contents_from_string(
    '''<html>
      <head>
        <title>Epic Win!</title>
      </head>
      <body>
        <h1>Epic Win!</h1>
      </body>
      </html>\n''', headers={'Content-Type': 'text/html'})
    k.set_acl('public-read')
    bucket.set_acl('public-read')
    bucket.configure_website('index.html')
    return bucket

def create_zone(r53_conn, domain):
    print('Creating Route 53 zone %s...' % domain)
    try:
        zone = r53_conn.create_zone(domain)
        nameservers = '\n'.join(zone.get_nameservers())
        print('Zone created successfully. Update your name servers to these:')
        print(nameservers)
        return zone
    except boto.route53.exception.DNSServerError, e:
        print('Error creating zone %s' % domain)
        print(e)
        sys.exit(1)

def add_apex_alias(r53_conn, zone):
    rrs = boto.route53.record.ResourceRecordSets(r53_conn, zone.id)
    change = rrs.add_change(action='CREATE',
                            name=zone.name,
                            type='A',
                            alias_hosted_zone_id=us_east_1_website_hosted_zone,
                            alias_dns_name=us_east_1_website_endpoint)
    try:
        response = rrs.commit()
        return response
    except boto.route53.exception.DNSServerError, e:
        return e

def add_cname_alias(r53_conn, zone_id, bucket_name, bucket_endpoint):
    rrs = boto.route53.record.ResourceRecordSets(r53_conn, zone_id)
    change = rrs.add_change(action='CREATE',
                            name=bucket_name,
                            type='CNAME',
                            ttl=60)
    change.add_value(bucket_endpoint)
    try:
        response = rrs.commit()
        return response
    except boto.route53.exception.DNSServerError, e:
        return e
 

if __name__ == '__main__':
    args = parse_args()
    dns_type = get_record_type(args.domain)
    if not dns_type:
        print('invalid domain name %s' % args.domain)
        sys.exit(1)
    s3_conn = boto.connect_s3(calling_format=ProtocolIndependentOrdinaryCallingFormat())
    # Using a custom calling format to avoid HTTPS bug - https://github.com/boto/boto/issues/421
    r53_conn = boto.connect_route53()

    zone_name = get_domain_apex(args.domain)
    zone = r53_conn.get_zone(zone_name)
    if not zone:
        zone = create_zone(r53_conn, zone_name)        
    print('Creating S3 bucket %s...' % args.domain)
    bucket = create_bucket(s3_conn, args.domain)
    if dns_type == 'apex':
        print('Making the A record of your zone apex point to its S3 bucket...')
        create_alias_response = add_apex_alias(r53_conn, zone)
    else:
        bucket_endpoint = bucket.get_website_endpoint()
        print('Creating CNAME pointing from %s to %s...' % (args.domain, bucket_endpoint))
        add_cname_alias(r53_conn, zone.id, args.domain, bucket_endpoint)
        
