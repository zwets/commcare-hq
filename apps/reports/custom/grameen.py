#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import inspect 

from django.template.loader import render_to_string
from django.db import connection
import settings

from xformmanager.models import Metadata, FormDefModel, ElementDefModel
from reports.models import Case, SqlReport
from reports.util import get_whereclause
from reports.custom.shared import monitoring_report, Mother

from pprint import pprint


'''Report file for custom Grameen reports'''
# see mvp.py for an explanation of how these are used.

# temporarily "privatizing" the name because grameen doesn't
# want this report to show up in the UI 
def _monitoring(request):
    '''Safe Pregnancy Monitoring Report'''
    safe_preg_case_name = "Grameen Safe Pregnancies"
    try:
        case = Case.objects.get(name=safe_preg_case_name)
    except Case.DoesNotExist:
        return '''Sorry, it doesn't look like the forms that this report 
                  depends on have been uploaded.'''
    
    return monitoring_report(request, case)

def _mother_summary(request):
    '''Individual Mother Summary'''
    # this is intentionally private, as it's only accessed from within other
    # reports that explicitly know about it.  We don't want to list it because
    # we don't know what id to use.
    safe_preg_case_name = "Grameen Safe Pregnancies"
    try:
        case = Case.objects.get(name=safe_preg_case_name)
    except Case.DoesNotExist:
        return '''Sorry, it doesn't look like the forms that this report 
                  depends on have been uploaded.'''
    if not "case_id" in request.GET:
        return '''Sorry, you have to specify a mother using the case id
                  in the URL.'''

    case_id = request.GET["case_id"]    
    data = case.get_data_map_for_case(case_id)
    mom = Mother(case, case_id, data)

    mother_name = request.GET["mother_name"]
    if mom.mother_name != mother_name:
        return '''<p class="error">Sorry it appears that this id has been used by the CHW for
                  more than one mother.  Unfortunately, this means we can't 
                  yet show you her data here.  Please remind your CHW's to 
                  use unique case Ids!</p> 
               '''

    attrs = [name for name in dir(mom) if not name.startswith("_")]
    attrs.remove("data_map")
    display_attrs = [attr.replace("_", " ") for attr in attrs]
    all_attrs = zip(attrs, display_attrs)
    mom.hi_risk_reasons = _get_hi_risk_reason(mom)
    
    # get attachment ID for SMS Sending UI
    # This sucks. But it's impossible to just get the ID from Mother or Cata, since the models seem to overwrite it with the "CHW|ID" format
    instance_id = data.values()[0][0]['id']
    form_def = ElementDefModel.objects.get(table_name="schema_intel_grameen_safe_motherhood_registration_v0_3").form
    try: 
        meta = Metadata.objects.get(formdefmodel=form_def, raw_data=instance_id)
        attach_id = meta.attachment.id
    except Metadata.DoesNotExist:
        # TODO handle this better
        attach_id = None
    
    return render_to_string("custom/grameen/mother_details.html", 
                            {"mother": mom, "attrs": all_attrs, "attach_id": attach_id,
                             "MEDIA_URL": settings.MEDIA_URL, # we pretty sneakly have to explicitly pass this
                             }) 
                             

def _get_hi_risk_reason(mom):
    reasons = []
    if (mom.mother_age >= 35): reasons.append("35 or older") 
    if (mom.mother_age <= 18): reasons.append("18 or younger")
    if (mom.mother_height == 'under_150'): reasons.append("mother height under 150cm")
    if (mom.previous_csection == 'yes'): reasons.append("previous c-section")
    if (mom.previous_newborn_death == 'yes'): reasons.append("previous newborn death")
    if (mom.previous_bleeding == 'yes'): reasons.append("previous bleeding")
    if (mom.previous_terminations >= 3): reasons.append("%s previous terminations" % mom.previous_terminations)
    if (mom.previous_pregnancies >= 5): reasons.append("%s previous pregnancies" % mom.previous_pregnancies)
    if (mom.heart_problems == 'yes'): reasons.append("heart problems")
    if (mom.diabetes == 'yes'): reasons.append("diabetes")
    if (mom.hip_problems == 'yes'): reasons.append("hip problems")
    if (mom.card_results_syphilis_result == 'positive'): reasons.append("positive for syphilis")
    if (mom.card_results_hepb_result == 'positive'): reasons.append("positive for hepb")
    if (mom.over_5_years == 'yes'): reasons.append("over 5 years since last pregnancy")
    if (mom.card_results_hb_test == 'below_normal'): reasons.append("low hb test")
    if (mom.card_results_blood_group == 'onegative'): reasons.append("o-negative blood group")
    if (mom.card_results_blood_group == 'anegative'): reasons.append("a-negative blood group")
    if (mom.card_results_blood_group == 'abnegative'): reasons.append("ab-negative blood group")
    if (mom.card_results_blood_group == 'bnegative'): reasons.append("b-negative blood group")
    return ", ".join(reasons)
    
def hi_risk_pregnancies(request, format_to_str=True):
    '''Hi-Risk Pregnancy Summary'''
    # just pass on to the helper view, but ensure that hi-risk is set to yes
    params = request.GET.copy()
    params["sampledata_hi_risk"]="yes"
    return _chw_submission_summary(request, params, format_to_str)
    
def chw_submission_details(request, format_to_str=True):
    '''Health Worker Submission Details'''
    return _chw_submission_summary(request, request.GET, format_to_str)


def followed_up(request, format_to_str=True):
    '''Followed Up - currently only used to display the total count in the chart view'''
    # just pass on to the helper view, but ensure that hi-risk is set to yes
    params = request.GET.copy()
    params["follow"]="yes"
    return _chw_submission_summary(request, params, format_to_str)


def _chw_submission_summary(request, params, format_to_str=True):
    # this was made a private method so that we can call it from multiple reports
    # with an extra parameter.
    
    # had to move this form a sql report to get in the custom annotations
    # this is a pretty ugly/hacky hybrid approach, and should certainly
    # be cleaned up
    
    # hard coded to our fixture.  bad bad!
    grameen_submission_details_id = 2
    # hard coded to our schema.  bad bad!
    form_def = ElementDefModel.objects.get(table_name="schema_intel_grameen_safe_motherhood_registration_v0_3").form
    report = SqlReport.objects.get(id=grameen_submission_details_id)
    cols = ('meta_username', 'sampledata_hi_risk')
    where_cols = dict([(key, val) for key, val in params.items() if key in cols])
    whereclause = get_whereclause(where_cols)

    follow_filter = None
    if "follow" in params:
        if params["follow"] == "yes":
            follow_filter = True
        elif params["follow"] == "no":
            follow_filter = False

    search_term = (params['search'].strip() if 'search' in params else '')

    if search_term != '':
        search = "sampledata_mother_name LIKE '%%" + search_term + "%%'" 
        if whereclause.strip() == '':
            whereclause = " WHERE %s" % search
        else:
            whereclause += " AND %s" % search

    cols, data = report.get_data({"whereclause": whereclause, "orderby" : "ORDER BY sampledata_mother_name ASC"})
    new_data = []

    for row in data:
        new_row_data = dict(zip(cols, row))
        row_id = new_row_data["Instance ID"]

        try: 
            meta = Metadata.objects.get(formdefmodel=form_def, raw_data=row_id)
        except Metadata.DoesNotExist:
            # TODO handle this better
            pass

        try:
            follow = meta.attachment.annotations.count() > 0
            if follow_filter is not None:
                if follow_filter and not follow:
                    # filtering on true, but none found, don't include this
                    continue
                elif not follow_filter and follow:
                    # filtering on false, but found follows, don't include this
                    continue
        
            new_row_data["Follow up?"] = "yes" if follow else "no"
            new_row_data["meta"] = meta
            new_row_data["attachment"] = meta.attachment
            new_data.append(new_row_data)
        except Exception:
            # print "no atachment for %s" % meta
            pass
    cols = cols[:6]
    
    # per PPT
    cols.remove('Case ID')
    cols.remove('Healthcare Worker')
    
    if not format_to_str:
        return cols, new_data    
    else:
        return render_to_string("custom/grameen/chw_submission_details.html", 
                            {"MEDIA_URL": settings.MEDIA_URL, # we pretty sneakly have to explicitly pass this
                             "columns": cols,
                             "data": new_data,
                             "search_term": search_term})
    

