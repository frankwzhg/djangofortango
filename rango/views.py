from datetime import datetime
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from rango.models import Category, Page
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm
from rango.bing_search import run_query

# Create your views here.

def index(request):
    # query the database for a list of All categories currently stored
    # Order the categories by no. likes in descending order
    # Retrieve the top 5 only - or all if less than 5
    # Place the list in our context dict dictionary which will passed to the template engine
    category_list = Category.objects.order_by('-likes')[:5]
    page_list = Page.objects.order_by('views')[:5]
    context_dict = {'categories': category_list, 'pages':page_list}

    # get the number of visits to the site
    # we use the cookie.get() function to obtain the visits cookie.
    # if the cookie exists, the value returned is casted to a integer
    # if the cookie doesn't exists, we default to zero and casted that

    visits = request.session.get('visits')
    if not visits:
        visits = 1
    reset_last_visit_time = False
    last_visit = request.session.get('last_visit')
    # Render the response and send it back
    # response = render(request, 'rango/index.html', context_dict)

    # Does the last_visit exist?
    if last_visit:
        # yes it does! get the cookie value
        # last_visit = request.COOKIES['last_visit']
        # Cast the value to python date/time object
        last_visit_time = datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")
        # last_visit_time = '2015-06-05 10:30:30'
        # if it't been more than one day since the last visit ...
        if (datetime.now()-last_visit_time).days > 0 :
            visits = visits + 1

            reset_last_visit_time = True
    else:
    #     Cookie last_visit does not exist, so flag that will be set
        reset_last_visit_time = True

        # context_dict['visit'] = visits

        #Obtain our Response object early so we can add cookie information.
        # response = render(request, 'rango/index.html', context_dict)
    if reset_last_visit_time:
        request.session['last_visit'] = str(datetime.now())
        request.session['visits'] = visits
    context_dict['visits'] = visits
    response = render(request, 'rango/index.html', context_dict)
    # Return response back to the user, updating any cookies that need changed.
    return response

def about(request):

    # return HttpResponse('Rango says here is the about page')
    return render(request, 'rango/about.html')

def category(request, category_name_slug):
    # Create a context dictionary which we can pass to the template rendering engine
    context_dict = {}
    context_dict['result_list'] = None
    context_dict['query'] = None
    if request.method == 'POST':
        query = request.POST['query'].strip()
        if query:
            result_list = run_query(query)
            context_dict['result_list'] = result_list
            context_dict['query'] = query
    try:
        # Can we find a category name slug with the given name?
        # If we can't, the .get() method raised a DoesNotExist exception
        # So the .get() method return one model instance or raise an exception
        category = Category.objects.get(slug=category_name_slug)
        context_dict['category_name'] = category.name


        # Rtrieve all of associated pages
        # Note that filter return >= 1 model instance.
        pages = Page.objects.filter(category=category)

        # Add our result list to template context under name pages
        context_dict['pages'] = pages

        # we also add category object from database to the context dictionary.
        # we'll use thie in the template to verify that category exist.
        context_dict['category'] = category
    except Category.DoesNotExist:
        # we get here if we have not find the specified category
        # Don't do anything - the template display the "no category" message for us
        pass
    # Go render the response and return it to the client
    return render(request, 'rango/category.html', context_dict)

def add_category(request):
    # A HTTP POST?
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        # Have we been provided with a valid form?
        if form.is_valid():
            # save the new category into database
            form.save(commit=True)

            # Now call the index() view
            # the user will be show the homepage
            return index(request)
        else:
            # The supplied form contained error - just print them to terminal
            print form.errors
    else:
        # if the form is not post, display the form to enter details.
        form = CategoryForm()

    # Bad form(or form detail), no form supplied ...
    # Render the form with error message (if any).
    return render(request, 'rango/add_category.html', {'form': form})

def add_page(request, category_name_slug):

    try:
        cat = Category.objects.get(slug = category_name_slug)
    except Category.DoesNotExist:
        cat = None

    if request.method == 'POST':
        form = PageForm(request.POST)

        if form.is_valid():
            if cat:
                page = form.save(commit=False)
                page.category = cat
                page.views = 0
                page.save()

                # probably better to use redirect here
                return category(request, category_name_slug)
        else:
            print form.errors

    else:
        form = PageForm()

    context_dict = {'form':form, 'category':cat}

    return render(request, 'rango/add_page.html', context_dict)


def register(request):

    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.

    registered = False

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.

        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        # If the two forms are valid...
        if user_form.is_valid() and profile_form.is_valid():

            # Save the user's form data to the database.
            user = user_form.save()

            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.

            user.set_password(user.password)
            user.save()

            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, we set commit=False.
            # This delays saving the model until we're ready to avoid integrity problems.

            profile = profile_form.save(commit=False)
            profile.user = user

            # Did the user provide a profile picture?
            # If so, we need to get it from the input form and put it in the UserProfile model.

            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            # Now we save the UserProfile model instance
            profile.save()

            # Update our variable to tell the template registration was successful.
            registered = True
        # Invalid form or forms - mistakes or something else?
        # Print problems to the terminal.
        # They'll also be shown to the user.
        else:
            print user_form.errors, profile_form.errors

        # Not a HTTP POST, so we render our form using two ModelForm instances.
        # These forms will be blank, ready for user input.
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    # Render the template depending on the context.
    return render(request,
                  'registration/registration_form.html',
                  {'user_form': user_form, 'profile_form': profile_form, 'registered': registered}
                  )


def user_login(request):
    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
                # We use request.POST.get('<variable>') as opposed to request.POST['<variable>'],
                # because the request.POST.get('<variable>') returns None, if the value does not exist,
                # while the request.POST['<variable>'] will raise key error exception
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)

         # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return HttpResponseRedirect('/rango/')
            else:
                # An inactive account was used - no logging in!
                return HttpResponse("Your Rango account is disabled")
        else:
            # Bad login details were provided. So we can't log the user in.
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login detail supplied")
    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render(request, 'registration/login.html', {})

@login_required
def restricted(request):
    return HttpResponse("Since you're logged in, you can see this text!")

# Use the login_required() decorator to ensure only those logged in can access the view.
@login_required
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)

    # Take the user back to the homepage.
    return HttpResponseRedirect('/rango/')

def search(request):
    result_list = []

    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            # Run our run_query function to get the result list!
            result_list = run_query(query)

    return render(request, 'rango/search.html', {'result_list': result_list})


def track_url(request):
    page_id = None
    url = '/rango/'
    if request.method == 'GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
            try:
                page = Page.objects.get(id=page_id)
                page.views = page.views + 1
                page.save()
                url = page.url
            except:
                pass

    return redirect(url)

@login_required
def like_category(request):

    cat_id = None
    if request.method == 'GET':
        cat_id = request.GET['category_id']

    likes = 0
    if cat_id:
        cat = Category.objects.get(id=int(cat_id))
        if cat:
            likes = likes + 1
            cat.likes = likes
            cat.save()
    return HttpResponse(likes)

def get_category_list(max_results=0, starts_with=''):
    cat_list = []
    if starts_with:
        cat_list = Category.objects.filter(name__istartswith=starts_with)

    if max_results > 0:
        if len(cat_list) > max_results:
            cat_list = cat_list[:max_results]

    return cat_list

def suggest_category(request):

    cat_list = []
    starts_with = ''
    if request.method == 'GET':
        starts_with = request.GET['suggestion']

    cat_list = get_category_list(8, starts_with)

    return render(request, 'rango/cats.html', {'cats': cat_list})

@login_required
def auto_add_page(request):
    cat_id = None
    url = None
    title = None
    context_dict = {}
    if request.method == 'GET':
        cat_id = request.GET['category_id']
        url = request.GET['url']
        title = request.GET['title']
        if cat_id:
            category = Category.objects.get(id=int(cat_id))
            p = Page.objects.get_or_create(category=category, title=title, url=url)

            pages = Page.objects.filter(category=category).order_by('-views')

            # Adds our results list to the template context under name pages.
            context_dict['pages'] = pages

    return render(request, 'rango/page_list.html', context_dict)