#!/usr/bin/env python
from flask import Flask, request, make_response
from flask.ext import restful
import requests
import apikey
from alexapy.request import *
from alexapy.response import *
import random
import re
import stockportfolio

# GLOBAL VARIABLE ASSIGNMENT
VERSION = '1.0'
SECRET_KEY = '1234'

# INITIALIZE FLASK APPLICATION
app = Flask(__name__)
api = restful.Api(app)
MASHAPE_API_KEY = apikey.MASHAPE_API_KEY

class StockQuote(restful.Resource):
    '''
    A Webservice for Amazon Alexa.  Provides:
    - A stock price given a ticker symbol (hard coded)
    TODO:
    - Speak ticker symbol to Alexa
    '''

    def post(self):
        obj = Request.from_json(request.json)
        response = self.stock_response(obj)
        return response

    def intent_mapping(self):
        return {
            'lookupbysymbol': self.lookup_by_symbol('csco'),
        }

    @api.representation('application/json')
    def stock_response(self, request_object):
        print request_object.request.type
        speak = "Welcome to Stock Quote"
        mysession = dict()
        if request_object.request.type == 'LaunchRequest':
            speak = speak + ".  This is a " + request_object.request.type + ". Please say a stock to lookup"
            mysession['intentSequence']= 'lookupbysymbol'
            endsession = False

        elif request_object.request.type == 'IntentRequest':
            ticker = request_object.request.intent['slots']['symbol']['value']
            ticker = (re.sub('\W+', '', ticker))
            data = self.lookup_by_symbol(ticker)
            if data['list']['meta']['count'] == 0:
                print("not a symbol")
                speak = "I'm sorry but %s is not a valid symbol" % ticker
            else:
                issure_name = data['list']['resources'][0]['resource']['fields']['issuer_name']
                price = '%.2f' % float(data['list']['resources'][0]['resource']['fields']['price'])
                speak = "The current price of %s is %s dollars" % (issure_name,price)
                endsession = True
        response = self.alexaspeak(speak, mysession, endsession)
        return response


    @staticmethod
    def alexaspeak(speak, mysession, endsession):
        mycard = Card("Stock Price", speak)
        myspeech = OutputSpeech(speak)
        response = Response(outputspeech=myspeech, card=mycard)
        mybody = ResponseBody(session=mysession, response=response, endsession=endsession)
        #print("**********************************************")
        resp = make_response(mybody.to_json(), 200)
        print(json.dumps(json.loads(mybody.to_json()), indent=4))
        resp.headers.extend({})
        return resp

    @staticmethod
    def lookup_by_symbol(symbol):
        response = requests.get("http://finance.yahoo.com/webservice/v1/symbols/%s/quote?format=json&view=detail" % symbol)
        data = json.loads(response.text)
        #print(data)
        return data

api.add_resource(StockQuote, '/api/stock')

if __name__ == '__main__':
    app.secret_key = SECRET_KEY
    app.run(host='0.0.0.0', debug=True)
