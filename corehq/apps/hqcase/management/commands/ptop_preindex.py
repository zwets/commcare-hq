from datetime import datetime
from django.core.mail import mail_admins
from gevent import monkey;monkey.patch_all()
import gevent
from gevent import Greenlet
from pillowtop.listener import AliasedElasticPillow
from pillowtop.management.pillowstate import get_pillow_states
from pillowtop.run_pillowtop import import_pillows
from django.core.management.base import NoArgsCommand, BaseCommand
from django.core.management import call_command
from django.conf import settings



def do_reindex(pillow_class_name):
    print "Starting pillow preindex %s" % pillow_class_name

    reindex_command = None
    if pillow_class_name == 'DomainPillow':
        reindex_command = 'ptop_fast_reindex_domains'
    elif pillow_class_name == 'CasePillow':
        reindex_command='ptop_fast_reindex_cases'
    elif pillow_class_name == 'FullCasePillow':
        reindex_command = 'ptop_fast_reindex_fullcases'
    elif pillow_class_name == 'XFormPillow':
        reindex_command = 'ptop_fast_reindex_xforms'
    elif pillow_class_name == 'FullXFormPillow':
        reindex_command = 'ptop_fast_reindex_fullxforms'

    call_command(reindex_command, **{'noinput': True, 'bulk': True, 'chunk_size': 25})
    print "Pillow preindex finished %s" % pillow_class_name


class Command(BaseCommand):
    help = "Preindex pillowtop ES"
    option_list = NoArgsCommand.option_list + ()

    def handle(self, *args, **options):
        runs = []
        pillows = import_pillows()
        aliased_pillows = filter(lambda x: isinstance(x, AliasedElasticPillow), pillows)

        mapped_masters, unmapped_masters, stale_indices = get_pillow_states(pillows)

        print "Master indices missing aliases:"

        unmapped_indices = [x[0] for x in unmapped_masters]

        reindex_pillows = filter(lambda x: x.es_index in unmapped_indices, aliased_pillows)

        print reindex_pillows

        if len(reindex_pillows) > 0:
            preindex_message = """
        Heads up!

        %sis going to start preindexing the following pillows:
        %s

        This may take a while, so don't deploy until all these have reported finishing.
            """ % (settings.EMAIL_SUBJECT_PREFIX, ', '.join([x.__class__.__name__ for x in reindex_pillows]))

            mail_admins("Pillow preindexing starting", preindex_message)
        else:
            mail_admins("Pillow preindexing completed", "All pillows are already up to date")



        start = datetime.utcnow()
        for pillow in reindex_pillows:
            print pillow.__class__.__name__
            g = gevent.spawn(do_reindex, pillow.__class__.__name__)
            runs.append(g)
        gevent.joinall(runs)
        if len(reindex_pillows) > 0:
            mail_admins("Pillow preindexing completed", "Reindexing %s took %s seconds" % (
                ', '.join([x.__class__.__name__ for x in reindex_pillows]),
                (datetime.utcnow() - start).seconds
            ))
        print "All pillowtop reindexing jobs completed"







