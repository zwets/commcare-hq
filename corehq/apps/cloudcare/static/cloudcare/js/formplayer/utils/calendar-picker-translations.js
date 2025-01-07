'use strict';
hqDefine('cloudcare/js/formplayer/utils/calendar-picker-translations', [
    'jquery',
    'calendars/dist/js/jquery.plugin',
    'calendars/dist/js/jquery.calendars',
    'calendars/dist/js/jquery.calendars.picker',
    'calendars/dist/js/jquery.calendars.ethiopian',
    'calendars/dist/js/jquery.calendars.plus',
    'calendars/dist/js/jquery.calendars-am',
    'calendars/dist/js/jquery.calendars.picker-am',
    'calendars/dist/js/jquery.calendars.ethiopian-am',
], function (
    $
) {
    // English
    $.calendarsPicker.regionalOptions[''] = { // Default regional settings - English/US
        renderer: $.calendarsPicker.regionalOptions[''].renderer, // this.defaultRenderer
        prevText: '&lt;Prev &nbsp; Month',
        prevStatus: 'Show the previous month',
        prevJumpText: '&lt;&lt;',
        prevJumpStatus: 'Show the previous year',
        nextText: 'Next&nbsp;Month&gt;',
        nextStatus: 'Show the next month',
        nextJumpText: '&gt;&gt;',
        nextJumpStatus: 'Show the next year',
        currentText: 'Current',
        currentStatus: 'Show the current month',
        todayText: 'Today',
        todayStatus: 'Show today\'s month',
        clearText: 'Clear',
        clearStatus: 'Clear all the dates',
        closeText: 'Close',
        closeStatus: 'Close the datepicker',
        yearStatus: 'Change the year',
        earlierText: '&#160;&#160;▲',
        laterText: '&#160;&#160;▼',
        monthStatus: 'Change the month',
        weekText: 'Wk',
        weekStatus: 'Week of the year',
        dayStatus: 'Select DD, M d, yyyy',
        defaultStatus: 'Select a date',
        isRTL: false,
    };
    $.calendars.calendars.ethiopian.prototype.regionalOptions[''] = {
        name: 'Ethiopian',
        epochs: ['BEE', 'EE'],
        monthNames: ['Meskerem', 'Tikemet', 'Hidar', 'Tahesas', 'Tir', 'Yekatit',
            'Megabit', 'Miazia', 'Genbot', 'Sene', 'Hamle', 'Nehase', 'Pagume'],
        monthNamesShort: ['Mes', 'Tik', 'Hid', 'Tah', 'Tir', 'Yek',
            'Meg', 'Mia', 'Gen', 'Sen', 'Ham', 'Neh', 'Pag'],
        dayNames: ['Ehud', 'Segno', 'Maksegno', 'Irob', 'Hamus', 'Arb', 'Kidame'],
        dayNamesShort: ['Ehu', 'Seg', 'Mak', 'Iro', 'Ham', 'Arb', 'Kid'],
        dayNamesMin: ['Eh', 'Se', 'Ma', 'Ir', 'Ha', 'Ar', 'Ki'],
        digits: null,
        dateFormat: 'dd/mm/yyyy',
        firstDay: 0,
        isRTL: false,
    };


    // Amharic
    $.calendarsPicker.regionalOptions['amh'] = {
        renderer: $.calendarsPicker.regionalOptions[''].renderer,
        prevText: 'ያለፈ',
        prevStatus: 'ያለፈውን ወር አሳይ',
        prevJumpText: '&lt;&lt;',
        prevJumpStatus: 'ያለፈውን ዓመት አሳይ',
        nextText: 'ቀጣይ',
        nextStatus: 'ቀጣዩን ወር አሳይ',
        nextJumpText: '&gt;&gt;',
        nextJumpStatus: 'ቀጣዩን ዓመት አሳይ',
        currentText: 'አሁን',
        currentStatus: 'የአሁኑን ወር አሳይ',
        todayText: 'የአሁኑ ወር',
        todayStatus: 'የዛሬን ወር አሳይ',
        clearText: 'አጥፋ',
        clearStatus: 'የተመረጠውን ቀን አጥፋ',
        closeText: 'ዝጋ',
        closeStatus: 'የቀን መምረጫውን ዝጋ',
        yearStatus: 'ዓመቱን ቀይር',
        earlierText: '&#160;&#160;▲',
        laterText: '&#160;&#160;▼',
        monthStatus: 'ወሩን ቀይር',
        weekText: 'ሳም',
        weekStatus: 'የዓመቱ ሳምንት ',
        dayStatus: 'DD M d yyyy ምረጥ',
        defaultStatus: 'ቀን ምረጥ',
        isRTL: false,
    };

    $.calendars.calendars.ethiopian.prototype.regionalOptions['amh'] = {
        name: 'የኢትዮጵያ ዘመን አቆጣጠር',
        epochs: ['BEE', 'EE'],
        monthNames: [
            "መስከረም",
            "ጥቅምት",
            "ህዳር",
            "ታህሳስ",
            "ጥር",
            "የካቲት",
            "መጋቢት",
            "ሚያዝያ",
            "ግንቦት",
            "ሰኔ",
            "ሃምሌ",
            "ነሃሴ",
            "ጷጉሜ",
        ],
        monthNamesShort: [
            "መስከረም",
            "ጥቅምት",
            "ህዳር",
            "ታህሳስ",
            "ጥር",
            "የካቲት",
            "መጋቢት",
            "ሚያዝያ",
            "ግንቦት",
            "ሰኔ",
            "ሃምሌ",
            "ነሃሴ",
            "ጷጉሜ",
        ],
        dayNames: [
            "እሁድ",
            "ሰኞ",
            "ማክሰኞ",
            "እሮብ",
            "ሃሙስ",
            "አርብ",
            "ቅዳሜ",
        ],
        dayNamesShort: [
            "እሁድ",
            "ሰኞ",
            "ማክሰኞ",
            "እሮብ",
            "ሃሙስ",
            "አርብ",
            "ቅዳሜ",
        ],
        dayNamesMin: [
            "እሁድ",
            "ሰኞ",
            "ማክሰኞ",
            "እሮብ",
            "ሃሙስ",
            "አርብ",
            "ቅዳሜ",
        ],
        digits: null,
        dateFormat: 'dd/mm/yyyy',
        firstDay: 0,
        isRTL: false,
    };

    // Tigrinya
    $.calendarsPicker.regionalOptions['tir'] = {
        renderer: $.calendarsPicker.regionalOptions[''].renderer,
        prevText: 'ዝሓለፈ',
        prevStatus: 'ናይ ዝሓለፈ ወርሒ አርኢ',
        prevJumpText: '&lt;&lt;',
        prevJumpStatus: 'ናይ ዝሓለፈ ዓመት አርኢ',
        nextText: 'ቐጺሉ',
        nextStatus: 'ቐጻሊ ወርሒ አርኢ',
        nextJumpText: '&gt;&gt;',
        nextJumpStatus: 'ቐጻሊ ዓመት አርኢ',
        currentText: 'ህሉው',
        currentStatus: 'ናይ ሕዚ ወርሒ አርኢ',
        todayText: 'ሎሚ',
        todayStatus: 'ናይ ሎሚ',
        clearText: 'ሰርዝ',
        clearStatus: 'ኩሎም ዕለታት ሰርዝ',
        closeText: 'ዕጸው',
        closeStatus: 'ዕለት መምረፂ ዕጸው',
        yearStatus: 'ዓመት ቐይሪ',
        earlierText: '&#160;&#160;▲',
        laterText: '&#160;&#160;▼',
        monthStatus: 'ወርሒ ቐይሪ',
        weekText: 'ሰሙን',
        weekStatus: 'ሰሙን ዓመት',
        dayStatus: 'DD M d yyyy ምረፂ',
        defaultStatus: 'ዕለት ምረፂ',
        isRTL: false,
    };
    $.calendars.calendars.ethiopian.prototype.regionalOptions['tir'] = {
        name: 'Ethiopian',
        epochs: ['BEE', 'EE'],
        monthNames: [
            "መስከረም",
            "ጥቅምቲ",
            "ሕዳር",
            "ታሕሳስ",
            "ጥሪ",
            "ለካቲት",
            "መጋቢት",
            "ምያዝያ",
            "ጉንበት",
            "ሰነ",
            "ሓምለ",
            "ነሓሰ",
            "ጳጉሜን",
        ],
        monthNamesShort: [
            "መስ",
            "ጥቅ",
            "ሕዳ",
            "ታሕ",
            "ጥሪ",
            "ለካ",
            "መጋቢት",
            "ምያ",
            "ጉን",
            "ሰነ",
            "ሓምለ",
            "ነሓሰ",
            "ጳጉሜን",
        ],
        dayNames: [
            "ሰንበት",
            "ሶኒ",
            "ሰሉስ",
            "ሮብዕ",
            "ሓሙስ",
            "ዓርቢ",
            "ቐዳም",
        ],
        dayNamesShort: [
            "ሰንበት",
            "ሶኒ",
            "ሰሉስ",
            "ሮብዕ",
            "ሓሙስ",
            "ዓርቢ",
            "ቐዳም",
        ],
        dayNamesMin: [
            "ሰንበት",
            "ሶኒ",
            "ሰሉስ",
            "ሮብዕ",
            "ሓሙስ",
            "ዓርቢ",
            "ቐዳም",
        ],
        digits: null,
        dateFormat: 'dd/mm/yyyy',
        firstDay: 0,
        isRTL: false,
    };

    // Oromo
    $.calendarsPicker.regionalOptions['orm'] = { // Default regional settings - English/US
        renderer: $.calendarsPicker.regionalOptions[''].renderer, // this.defaultRenderer
        prevText: 'kan darbe',
        prevStatus: 'baati darbe agarsisii',
        prevJumpText: '&lt;&lt;',
        prevJumpStatus: 'bara darbe agarsisii',
        nextText: 'itti aane dhufu',
        nextStatus: 'baati itti aanu agarsisii',
        nextJumpText: '&gt;&gt;',
        nextJumpStatus: 'bara itti aanu agarsisii',
        currentText: 'amma',
        currentStatus: 'baati ammaa agarsisii',
        todayText: 'har\'a',
        todayStatus: 'baati akka har\'aa',
        clearText: 'haqi',
        clearStatus: 'guyyaa filatame haqi',
        closeText: 'cufi',
        closeStatus: 'filattuu guyyaa cufi',
        yearStatus: 'bara jijjiiri',
        earlierText: '&#160;&#160;▲',
        laterText: '&#160;&#160;▼',
        monthStatus: 'baati jijjiri',
        weekText: 'Torbaan',
        weekStatus: 'Torbaan wagga',
        dayStatus: 'GG/JJ/Bar',
        defaultStatus: 'guyyaa filadhuu',
        isRTL: false,
    };
    $.calendars.calendars.ethiopian.prototype.regionalOptions['orm'] = {
        name: 'Ethiopian',
        epochs: ['BEE', 'EE'],
        monthNames: [
            "Fulbaana",
            "Onkololessa",
            "sadaasaa",
            "muddee",
            "Amajjii",
            "Gurandhala",
            "Bitootessaa",
            "Ebla",
            "Caamsaa",
            "Waxabajjii",
            "Adoolessa",
            "Hagayya",
            "Qaam'ee",
        ],
        monthNamesShort: [
            "Ful",
            "Onk",
            "Sad",
            "Mud",
            "Amaj",
            "Gur",
            "Bit",
            "Eb",
            "Cam",
            "Wax",
            "Adol",
            "Hag",
            "Qam",
        ],
        dayNames: [
            "Dulbata",
            "Wixata",
            "Kibxata",
            "Roobii",
            "Kamisa",
            "Jimaata",
            "Sanbata Duraa",
        ],
        dayNamesShort: [
            "Dilb",
            "Wix",
            "Kibx",
            "Roob",
            "Kam",
            "Jim",
            "San.D",
        ],
        dayNamesMin: [
            "Dilb",
            "Wix",
            "Kibx",
            "Roob",
            "Kam",
            "Jim",
            "San.D",
        ],
        digits: null,
        dateFormat: 'dd/mm/yyyy',
        firstDay: 0,
        isRTL: false,
    };
});
