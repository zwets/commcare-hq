hqDefine("geospatial/js/case_grouping_map",[
    "jquery",
    "knockout",
    'underscore',
    'hqwebapp/js/initial_page_data',
], function (
    $,
    ko,
    _,
    initialPageData
) {

    function caseModel(caseId, coordiantes, caseLink) {
        'use strict';
        var self = {};
        self.caseId = caseId;
        self.coordinates = coordiantes;
        self.caseLink = caseLink;

        // TODO: Group ID needs to be set
        self.groupId = null;

        return self;
    }

    function exportModel() {
        var self = {};

        self.casesToExport = ko.observableArray([]);

        self.handleExportCSV = function () {
            const casesToExport = _.map(self.casesToExport(), function (caseItem) {
                const coordinates = (caseItem.coordinates) ? `${caseItem.coordinates.lng} ${caseItem.coordinates.lat}` : "";
                return {
                    'groupId': caseItem.groupId,
                    'caseId': caseItem.caseId,
                    'coordinates': coordinates,
                };
            });
            exportToCsv(casesToExport);
        };

        // If list of propertiesToInclude is not given, will export all properties of objects in itemsArr
        function exportToCsv(itemsArr, includeHeaders = true) {
            if (!itemsArr.length) {
                return;
            }

            let csvStr = "";
            if (includeHeaders) {
                csvStr = Object.keys(itemsArr[0]).join(",");
                csvStr += "\n";
            }

            _.forEach(itemsArr, function (itemRow) {
                csvStr += Object.keys(itemRow).map(key => itemRow[key]).join(",");
                csvStr += "\n";
            });

            // Download CSV file
            const hiddenElement = document.createElement('a');
            hiddenElement.href = 'data:text/csv;charset=utf-8,' + encodeURI(csvStr);
            hiddenElement.target = '_blank';
            hiddenElement.download = `cases_by_group (created on ${getTodayDate()}).csv`;
            hiddenElement.click();
            hiddenElement.remove();
        }

        return self;
    }

    function getTodayDate() {
        const todayDate = new Date();
        const day = String(todayDate.getDate()).padStart(2, '0');
        const month = String(todayDate.getMonth() + 1).padStart(2, '0');  // January is 0
        const year = todayDate.getFullYear();
        return `${year}-${month}-${day}`;
    }

    $(function () {
        let caseModels = [];

        // Parses a case row (which is an array of column values) to an object, using caseRowOrder as the order of the columns
        function parseCaseItem(caseItem, caseRowOrder) {
            let caseObj = {};
            for (const propKey in caseRowOrder) {
                const propIndex = caseRowOrder[propKey];
                caseObj[propKey] = caseItem[propIndex];
            }
            return caseObj;
        }

        function loadCases(rawCaseData) {
            caseModels = [];
            const caseRowOrder = initialPageData.get('case_row_order');
            for (const caseItem of rawCaseData) {
                const caseObj = parseCaseItem(caseItem, caseRowOrder);
                const caseModelInstance = new caseModel(caseObj.case_id, caseObj.gps_point, caseObj.link);
                caseModels.push(caseModelInstance);
            }
        }

        $(document).ajaxComplete(function (event, xhr, settings) {
            const isAfterDataLoad = settings.url.includes('geospatial/json/case_grouping_map/');
            if (!isAfterDataLoad) {
                return;
            }

            // Hide the datatable rows but not the pagination bar
            $('.dataTables_scroll').hide();

            const caseData = xhr.responseJSON.aaData;
            if (caseData.length) {
                loadCases(caseData);
            }
        });
    });
});