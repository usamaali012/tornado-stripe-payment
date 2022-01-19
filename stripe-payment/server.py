import tornado
from tornado.web import Application
from tornado import ioloop
from apis import LandingPageHandler, SuccessPageHandler, CancelPageHandler, CreateCheckoutSessionHandler,\
    CustomPaymentHandler, StripeIntentView, WebHookHandler #,stripe_webhook


class MyServer(Application):
    def __init__(self):
        handler = self.GetHandler()

        Application.__init__(self, handler)

    def GetHandler(self):
        handler = [
            (r"/", LandingPageHandler),
            (r"/success", SuccessPageHandler),
            (r"/cancel", CancelPageHandler),
            (r"/create-checkout-session/(.*)", CreateCheckoutSessionHandler),
            (r"/custom-payment", CustomPaymentHandler),
            (r"/create-payment-intent/(.*)", StripeIntentView),
            # (r"/webhooks/stripe", stripe_webhook),
            (r"/webhooks/stripe", WebHookHandler)
        ]

        return handler

    def start_server(self):
        self.listen(8080)
        print("Port running at 8080")
        tornado.ioloop.IOLoop.current().start()

