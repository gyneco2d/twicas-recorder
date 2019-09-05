#!/usr/bin/env python
# -*- coding:utf-8 -*-

import argparse
import base64
import json
import os
import requests
import subprocess
from dotenv import load_dotenv
from http.server import BaseHTTPRequestHandler, HTTPServer

class Recorder(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            if self.headers.get('expect') == '100-continue':
                self.send_response(100)

                encoded_key = base64.b64encode(f"{os.environ['CLIENT_ID']}:{os.environ['CLIENT_SECRET']}".encode('utf-8')).decode('utf-8')
                headers = {
                    'Accept': 'application/json',
                    'X-Api-Version': '2.0',
                    'Authorization': f"Basic {encoded_key}"
                }
                payload = {
                    'lang': 'ja',
                    'words': f"{os.environ['TARGET_USER']}"
                }
                r = requests.get(f"{os.environ['BASE_URL']}/users/{os.environ['TARGET_USER']}", headers=headers, params=payload)
                user = r.json()['user']
                if user['is_live']:
                    print('target_user now live')
                    r = requests.get(f"{os.environ['BASE_URL']}/users/{os.environ['TARGET_USER']}/current_live", headers=headers)
                    movie = r.json()['movie']
                    broadcaster = r.json()['broadcaster']

                    args = [
                        'ffmpeg',
                        '-i',
                        f"https://twitcasting.tv/{broadcaster['screen_id']}/metastream.m3u8/?video=1",
                        '-movflags',
                        'faststart',
                        '-c',
                        'copy',
                        '-bsf:a',
                        'aac_adtstoasc',
                        f"{movie['id']}.mp4"
                    ]
                    res = subprocess.call(args)

                print('target_user no longer live')
                return

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = { 'status': 200 }
            responseBody = json.dumps(response)

            self.wfile.write(responseBody.encode('utf-8'))

        except Exception as e:
            print("An error occured")
            print("The information of error is as following")
            print(type(e))
            print(e.args)
            print(e)
            response = {
                'status': 500,
                'msg': 'An error occured'
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            responseBody = json.dumps(response)

            self.wfile.write(responseBody.encode('utf-8'))


def importargs():
    parser = argparse.ArgumentParser("This is the simple server")

    parser.add_argument('--host', '-H', required=False, default='localhost')
    parser.add_argument('--port', '-P', required=False, type=int, default=8080)

    args = parser.parse_args()

    return args.host, args.port


def run(server_class=HTTPServer, handler_class=Recorder, server_name='localhost', port=8080):

    server = server_class((server_name, port), handler_class)
    server.serve_forever()


def main():
    load_dotenv()
    host, port = importargs()
    run(server_name=host, port=port)


if __name__ == '__main__':
    main()
