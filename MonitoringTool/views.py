""" Views for the app using Jinja2. """
from urllib import request, response
from fastapi import Request
from fastapi.templating import Jinja2Templates

class BaseView:
    """ Base class for views

    This class handles the initialization of Jinja2Templates and provides
    a method for rendering templates based on the class name.

    """
    def __init__(self):
        """ Initializes Jinja2Templates with the specified directory. """
        self.templates = Jinja2Templates(directory="MonitoringTool/static")

    @property
    def template_name(self):
        """ Dynamically derives the template name from the class name. """
        return f"{self.__class__.__name__.lower().replace('view', '')}.html"

    def render(self, request: Request, response : dict):
        """ Renders a template with the provided request and response. """
        return self.templates.TemplateResponse(self.template_name, {"request": request, **response})

class ResultsView(BaseView):
    """ View for displaying endpoints of the monitoring tool. """
    def render(self, request: Request, **response):
        return super().render(request, {"results" : response.get('results',[])})

class HistoryView(BaseView):
    """ View for displaying history of an endpoint """
    def render(self, request: Request, **response):
        return super().render(request, {"checks" : response.get('checks',[])})
    