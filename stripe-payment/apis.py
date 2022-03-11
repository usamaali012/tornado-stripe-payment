import json
import traceback

import stripe
import tornado
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from tornado.web import RequestHandler
from tornado.httpclient import HTTPResponse
from models.product_models import Base, Price



STRIPE_PUBLIC_KEY = "ENTER STRIPE_PUBLIC_KEY"
STRIPE_SECRET_KEY = "ENTER STRIPE_SECRET_KEY"
STRIPE_WEBHOOK_SECRET = "ENTER STRIPE_WEBHOOK_SECRET"

stripe.api_key = STRIPE_SECRET_KEY


class MainApiHandler(RequestHandler):
    def prepare(self):
        super().prepare()
        self.gdb = None
        self.get_db_connection()

    def get_db_connection(self):
        try:
            engine = create_engine("mysql+mysqlconnector://root:1234@localhost/products")
            if not database_exists(engine.url):
                create_database(engine.url)

            Base.metadata.create_all(engine)

            Session = sessionmaker(bind=engine)
            self.gdb = Session()
            print('Database Connection Established...')

        except Exception:
            traceback.print_exc()
            raise tornado.web.HTTPError(503)


class LandingPageHandler(MainApiHandler):
    def get(self):
        price = self.gdb.query(Price).filter(Price.product_id == 1).one_or_none()
        self.render('templates/landing.html', price=price)


class SuccessPageHandler(RequestHandler):
    def get(self):
        self.render('templates/success.html')


class CancelPageHandler(RequestHandler):
    def get(self):
        self.render('templates/cancel.html')


class CreateCheckoutSessionHandler(MainApiHandler):
    def post(self, *args, **kwargs):
        YOUR_DOMAIN = 'http://127.0.0.1:8080'
        pk = args[0]
        price = self.gdb.query(Price).filter(Price.product_id == pk).one_or_none()
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        'price': price.stripe_price_id,
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=YOUR_DOMAIN + '/success',
                cancel_url=YOUR_DOMAIN + '/cancel',
            )
        except Exception as e:
            return str(e)

        self.redirect(checkout_session.url)
        return


class StripeIntentView(MainApiHandler):
    def post(self, *args, **kwargs):
        try:
            req_json = json.loads(self.request.body)
            price = self.gdb.query(Price).filter(Price.product_id == 1).one_or_none()
            customer = stripe.Customer.create(email=req_json['email'])
            intent = stripe.PaymentIntent.create(
                amount='90',
                currency='usd',
                customer=customer['id'],
                metadata={
                    "price_id": price.stripe_price_id
                }
            )
            return self.write(json.dumps({
                'clientSecret': intent['client_secret']
            }))

        except Exception as e:
            print('error:', str(e))
            return self.write(json.dumps({'error': e}))



class CustomPaymentHandler(MainApiHandler):
    def get(self):
        price = self.gdb.query(Price).filter(Price.product_id == 1).one_or_none()
        self.render('templates/custom_payment.html', public_key=STRIPE_PUBLIC_KEY, price=price)


class WebHookHandler(MainApiHandler):
    def post(self, *args, **kwargs):
        self.stripe_webhook(self.request)


    def stripe_webhook(self, request):
        request.url = request.uri
        payload = (request.body, 'body')
        sig_header = request.headers.get('Stripe-Signature')
        event = None
        try:
            event = stripe.Webhook.construct_event(
                payload[0], sig_header, STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            # Invalid payload
            print(':', str(e))
            return HTTPResponse(request, 400, error=e)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            print('Invalid signature:', str(e))
            return HTTPResponse(request, 400, error=e)

        # Handle the checkout.session.completed event
        if event['type'] == 'checkout.session.completed':
            print('going to success page')
            session = event['data']['object']
            customer_email = session["customer_details"]["email"]
            line_items = stripe.checkout.Session.list_line_items(session["id"])

            stripe_price_id = line_items["data"][0]["price"]["id"]

            print(customer_email, stripe_price_id)

        elif event["type"] == "payment_intent.succeeded":
            print('payment intent succeeded')
            intent = event['data']['object']

            stripe_customer_id = intent["customer"]
            stripe_customer = stripe.Customer.retrieve(stripe_customer_id)

            customer_email = stripe_customer['email']

            print(stripe_customer_id, customer_email)

        return HTTPResponse(request, 200)
