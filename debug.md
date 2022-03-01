- turbo-frame redirects are a bit confusing, but I found this resource that was helpful: https://turbo.hotwired.dev/handbook/frames#targeting-navigation-into-or-out-of-a-frame. 

https://discuss.hotwired.dev/t/form-redirects-not-working-as-expected/2058

When I want to redirect from my register-form or login-form, I need to set the target="_top" on the turbo-frame, but then it only allows me to redirect on success, but not show the errors... 
    - for now, the solution is to show error messages with turbo streams, and use _top to redirect. This means that for right now, when there are errors, I return a 400 with a string message and the page doesn't change. This is working, but I see 
```javascript
turbo.js:17 Error: Form responses must redirect to another location
    at A.requestSucceededWithResponse (turbo.js:3:6617)
``` 
in the dev console of the browser, which seems bad... oh well for now. 

## Dealing with login in pytest
I couldn't get the first test_match function to work on login, it kept trying to redirect me to login when I was trying to create a new group...
I added this func to conftest.py
```python
@pytest.fixture()
def test_with_authenticated_user(app):
    @login_manager.request_loader
    def load_user_from_request(request):
        return User.query.first()
```
which I got from this github issue: https://github.com/pytest-dev/pytest-flask/issues/40#issuecomment-447061393
I don't really get what's going on... but it is working for now


## More issues with forms and turbo-streams
I just accidentally put the Create Account button on the register match page. When this happened, I could hit create account, it would submit, I get a 200, but then the errors aren't streamed to the right place... it's a weird thing and I'm not sure how to handle it yet, especially if I can only returna  200 for that.. I might need to do some javascript stuff