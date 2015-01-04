import datetime

from django.core.urlresolvers import reverse
from django.conf import settings
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required

import stripe

from .forms import CardForm
from .models import GoldUser

stripe.api_key = settings.STRIPE_SECRET


def soon():
    soon = datetime.date.today() + datetime.timedelta(days=30)
    return {'month': soon.month, 'year': soon.year}


@login_required
def register(request):
    user = request.user
    try:
        gold_user = GoldUser.objects.get(user=request.user)
    except:
        gold_user = None
    if request.method == 'POST':
        form = CardForm(request.POST)
        if form.is_valid():

            customer = stripe.Customer.create(
                description=user.username,
                email=user.email,
                card=form.cleaned_data['stripe_token'],
                plan=form.cleaned_data['level'],
            )

            user = GoldUser(
                user=request.user,
                level=form.cleaned_data['level'],
                last_4_digits=form.cleaned_data['last_4_digits'],
                stripe_id=customer.id,
                subscribed=True,
            )

            try:
                user.save()
            except IntegrityError:
                form.addError(user.email + ' is already a member')
            else:
                return HttpResponseRedirect(reverse('gold_register'))

    else:
        form = CardForm()

    return render_to_response(
        'gold/register.html',
        {
            'form': form,
            'gold_user': gold_user,
            'publishable': settings.STRIPE_PUBLISHABLE,
            'soon': soon(),
            'user': user,
            'months': range(1, 13),
            'years': range(2011, 2036),
        },
        context_instance=RequestContext(request)
    )


@login_required
def edit(request):
    user = GoldUser.objects.get(user=request.user)
    if request.method == 'POST':
        form = CardForm(request.POST)
        if form.is_valid():

            customer = stripe.Customer.retrieve(user.stripe_id)
            customer.card = form.cleaned_data['stripe_token']
            customer.save()

            user.last_4_digits = form.cleaned_data['last_4_digits']
            user.stripe_id = customer.id
            user.save()

            return HttpResponseRedirect(reverse('gold_register'))

    else:
        form = CardForm()

    return render_to_response(
        'gold/edit.html',
        {
            'form': form,
            'publishable': settings.STRIPE_PUBLISHABLE,
            'soon': soon(),
            'months': range(1, 13),
            'years': range(2011, 2036)
        },
        context_instance=RequestContext(request)
    )
