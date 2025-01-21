from django.db import migrations
from django.db.migrations import RunPython

from corehq.motech.const import ALGO_AES, ALGO_AES_CBC
from corehq.util.django_migrations import skip_on_fresh_install
from corehq.motech.utils import (
    reencrypt_ecb_to_cbc_mode,
    reencrypt_cbc_to_ecb_mode,
    b64_aes_cbc_encrypt,
    AesEcbDecryptionError
)


@skip_on_fresh_install
def migrate_api_settings(apps, schema_editor):
    ConnectionSettings = apps.get_model("motech", "ConnectionSettings")

    connect_settings_to_update = ConnectionSettings.objects.exclude(
        password__startswith=f'${ALGO_AES_CBC}$',
        client_secret__startswith=f'${ALGO_AES_CBC}$',
        last_token_aes__startswith=f'${ALGO_AES_CBC}$',
    ).exclude(
        password='',
        client_secret='',
        last_token_aes=''
    )

    for connection in connect_settings_to_update:
        connection.password = _reencrypt_or_encrypt_value_with_cbc(connection.password)
        connection.client_secret = _reencrypt_or_encrypt_value_with_cbc(connection.password)
        connection.last_token_aes = _reencrypt_value_with_cbc(connection.last_token_aes)
        connection.save()


def _reencrypt_or_encrypt_value_with_cbc(value):
    if value == '':
        return ''
    if value.startswith(f'${ALGO_AES_CBC}$'):
        return value

    if value.startswith(f'${ALGO_AES}$'):
        try:
            return reencrypt_ecb_to_cbc_mode(value, f'${ALGO_AES}$')
        except AesEcbDecryptionError:
            return ''
    else:
        ciphertext = b64_aes_cbc_encrypt(value)
        return f'${ALGO_AES_CBC}${ciphertext}'


def _reencrypt_value_with_cbc(value):
    if value == '':
        return ''
    if value.startswith(f'${ALGO_AES_CBC}$'):
        return value

    if value.startswith(f'${ALGO_AES}$'):
        prefix = f'${ALGO_AES}$'
    else:
        prefix = None
    try:
        return reencrypt_ecb_to_cbc_mode(value, prefix)
    except AesEcbDecryptionError:
        return ''


def revert_api_settings(apps, schema_editor):
    ConnectionSettings = apps.get_model("motech", "ConnectionSettings")

    connect_settings_to_revert = ConnectionSettings.objects.exclude(
        password__startswith=f'${ALGO_AES}$',
        client_secret__startswith=f'${ALGO_AES}$',
        last_token_aes__startswith=f'${ALGO_AES}$',
    ).exclude(
        password='',
        client_secret='',
        last_token_aes=''
    )

    for connection in connect_settings_to_revert:
        connection.password = _revert_reencrypted_value_to_ecb(connection.password)
        connection.client_secret = _revert_reencrypted_value_to_ecb(connection.client_secret)
        connection.last_token_aes = _revert_last_token_to_ecb(connection.last_token_aes)
        connection.save()


def _revert_reencrypted_value_to_ecb(value):
    if value == '':
        return ''
    elif value.startswith(f'${ALGO_AES_CBC}$'):
        return reencrypt_cbc_to_ecb_mode(value, f'${ALGO_AES_CBC}$')
    else:
        return value


def _revert_last_token_to_ecb(value):
    if value == '':
        return ''
    elif value.startswith(f'${ALGO_AES_CBC}$'):
        encrypted_val = reencrypt_cbc_to_ecb_mode(value, f'${ALGO_AES_CBC}$')
        # last_token_aes is originally only stored without a prefix
        return encrypted_val.split('$', 2)[2]
    else:
        return value


class Migration(migrations.Migration):

    dependencies = [
        ('motech', '0016_connectionsettings_include_client_id_and_more'),
    ]

    operations = [
        RunPython(migrate_api_settings, reverse_code=revert_api_settings),
    ]
