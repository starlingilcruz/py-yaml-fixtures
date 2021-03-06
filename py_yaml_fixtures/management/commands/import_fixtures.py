import os

from django.apps import apps
from django.core.management.base import BaseCommand

from py_yaml_fixtures import FixturesLoader
from py_yaml_fixtures.factories.django import DjangoModelFactory
from py_yaml_fixtures.fixtures_loader import MULTI_CLASS_FILENAMES, REQUIRED_FILENAMES


class Command(BaseCommand):

    help = 'Import Jinja2-templated YAML database fixtures from apps'

    def add_arguments(self, parser):
        parser.add_argument(
            'apps', nargs='*', help='App names to load from (defaults to all)'
        )

        parser.add_argument(
            '--required',
            action='store_true',
            default=False,
            dest="required",
            help='Load only required fixtures',
        )

        parser.add_argument(
            '--load',
            type=str,
            dest="load",
            help='Load only specified file names',
        )

    def handle(self, *args, **options):
        models = []
        fixture_dirs = []
        apps_with_fixtures = set()
        default_file_names = MULTI_CLASS_FILENAMES

        required = options.get('required')

        if required:
            default_file_names = REQUIRED_FILENAMES

        file_to_load = options.get("load")

        if file_to_load:
            default_file_names = {file_to_load}

        app_names = options.get('apps')
        app_configs = ([
            apps.get_app_config(app_name) for app_name in app_names
        ] if app_names else apps.get_app_configs())
        for app_config in app_configs:
            models.extend(app_config.get_models())
            fixtures_dir = os.path.join(app_config.path, 'fixtures')
            if os.path.exists(fixtures_dir):
                fixture_dirs.append(fixtures_dir)
                apps_with_fixtures.add(app_config.name)
            for filename in MULTI_CLASS_FILENAMES:
                if os.path.exists(os.path.join(app_config.path, filename)):
                    if app_config.path not in fixture_dirs:
                        fixture_dirs.append(app_config.path)

        if not fixture_dirs:
            print('No fixtures found. Exiting.')
            return

        print(
            'Loading fixtures from apps: ' +
            ', '.join(sorted(apps_with_fixtures))
        )
        factory = DjangoModelFactory(models)
        loader = FixturesLoader(
            factory,
            fixture_dirs=fixture_dirs,
            file_names=default_file_names,
        )
        loader.create_all(lambda identifier, model, created: print(
            '{action} {identifier}: {model}'.format(
                action='Creating' if created else 'Updating',
                identifier=identifier.key,
                model=repr(model)
            )))
        print('Done loading fixtures. Exiting.')
