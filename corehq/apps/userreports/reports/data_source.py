from sqlagg import (
    ColumnNotFoundException,
    TableNotFoundException,
    SumWhen,
)
import sqlalchemy
from sqlalchemy.exc import ProgrammingError
from corehq.db import Session
from corehq.apps.reports.sqlreport import SqlData, DatabaseColumn
from corehq.apps.userreports.exceptions import UserReportsError
from corehq.apps.userreports.models import DataSourceConfiguration
from corehq.apps.userreports.sql import get_table_name
from dimagi.utils.decorators.memoized import memoized


def get_expanded_columns(table_name, filters, filter_values, column_config):

    session = Session()
    connection = session.connection()
    metadata = sqlalchemy.MetaData()
    metadata.reflect(bind=connection)

    column = metadata.tables[table_name].c[column_config.get_sql_column().view.name]
    query = sqlalchemy.select([column]).distinct()

    result = connection.execute(query, filter_values).fetchall()
    distinct_values = [x[0] for x in result]

    columns = []
    for val in distinct_values:
        columns.append(DatabaseColumn(
            u"{}-{}".format(column_config.display, val),
            SumWhen(
                column_config.field,
                whens={val: 1},
                else_=0,
                # TODO: What is the proper alias?
                # It looks like this alias needs to match data_slug
                alias=u"{}-{}".format(column_config.field, val),
            ),
            sortable=False,
            # TODO: Should this be column_config.report_column_id?
            # It looks like this data_slug needs to match alias
            data_slug=u"{}-{}".format(column_config.field, val),
            format_fn=column_config.get_format_fn(),
            help_text=column_config.description
        ))
    return columns


class ConfigurableReportDataSource(SqlData):

    def __init__(self, domain, config_or_config_id, filters, aggregation_columns, columns):
        self.domain = domain
        if isinstance(config_or_config_id, DataSourceConfiguration):
            self._config = config_or_config_id
            self._config_id = self._config._id
        else:
            assert isinstance(config_or_config_id, basestring)
            self._config = None
            self._config_id = config_or_config_id

        self._filters = {f.slug: f for f in filters}
        self._filter_values = {}
        self.aggregation_columns = aggregation_columns
        self.column_configs = columns

    @property
    def config(self):
        if self._config is None:
            self._config = DataSourceConfiguration.get(self._config_id)
        return self._config

    @property
    def table_name(self):
        return get_table_name(self.domain, self.config.table_id)

    @property
    def filters(self):
        return [fv.to_sql_filter() for fv in self._filter_values.values()]

    def set_filter_values(self, filter_values):
        for filter_slug, value in filter_values.items():
            self._filter_values[filter_slug] = self._filters[filter_slug].create_filter_value(value)

    @property
    def filter_values(self):
        return {k: v for fv in self._filter_values.values() for k, v in fv.to_sql_values().items()}

    @property
    def group_by(self):
        return self.aggregation_columns

    @property
    @memoized
    def columns(self):
        ret = []
        for conf in self.column_configs:
            if conf.aggregation == "expand":
                ret += get_expanded_columns(self.table_name, self.filters, self.filter_values, conf)
            else:
                ret.append(conf.get_sql_column())
        return ret

    @memoized
    def get_data(self, slugs=None):
        try:
            ret = super(ConfigurableReportDataSource, self).get_data(slugs)
            for report_column in self.column_configs:
                if report_column.format == 'percent_of_total':
                    column_name = report_column.get_sql_column().view.name
                    total = sum(row[column_name] for row in ret)
                    for row in ret:
                        row[column_name] = '{:.0%}'.format(
                            float(row[column_name]) / total
                        )
        except (
            ColumnNotFoundException,
            TableNotFoundException,
            ProgrammingError,
        ) as e:
            raise UserReportsError(e.message)
        # arbitrarily sort by the first column in memory
        # todo: should get pushed to the database but not currently supported in sqlagg
        return sorted(ret, key=lambda x: x[self.column_configs[0].report_column_id])

    def get_total_records(self):
        return len(self.get_data())
