// Here we have all GLOBAL Variables

/* General*/

var G_IsDebugging = 1;
var G_EnableAnalytics = 0;
var G_EnableReminders = 1;

var G_ShowAds = 0;
var G_TestingAds = false;


var G_Admobid = {};

///////////////////////////////////////////
// REAL ADS
//////////////////////////////////////////

G_Admobid = { // for Android
    banner: 'ca-app-pub-9756417211967452/1932692529',
    interstitial: 'ca-app-pub-9756417211967452/5667675980'
};





///////////////////////////////////////////
// TEST ADS
//////////////////////////////////////////
/*
G_Admobid = { // for Android
    banner: 'ca-app-pub-3940256099942544/6300978111',
    interstitial: 'ca-app-pub-3940256099942544/1033173712'
};
*/

var G_TimeSinceAppStarted = new Date();
var G_InterstitialPrepared = 0;
var G_InterstitialIsReady = 0;
var G_InterstitialShowed = 0;

var G_WasBannerShowed = 0;
var G_TimeSinceInterstitialShowed = new Date();
var G_TimesInterstitialWasShowed = 0;

var G_currentScreen = 'mainscreen'; // used to identify location of the user inside the app
var G_PreviousScreen = 'mainscreen';



//confirmation containers
var G_DeleteEntryConfirmation = 0;
var G_ChooseImageConfirmation = 0;
var G_DeleteImageConfirmation = 0;
var G_VisibleMainScreenAddButtons = 0;
var G_DeleteIncomeCategoryConfirmation = 0;
var G_DeleteExpenseCategoryConfirmation = 0;


var G_DeleteReminderConfirmation = 0;
var G_AddTransactionBarConfirmation = 0;
var G_ChoseTimeFrameBar = 0;
var G_selectedCurrencyFormat = 1;
var G_ResetLoginPasswordConfirmation = 0;
var G_ExitConfirmationScreen = 0;
var G_DeleteAllAppData = 0;

//used to decide how many time are the helping messages displayed
var G_MessageOccurances = 3;

var G_K = 'SEE$#!FAWDW()(@#<>';
var G_K2 = '!@#$%^&*!@#$FFFGTWSDEX?';


var G_d = '.';
var G_t = ',';

//image related
var G_DiaryFolderName = 'ExpenseManagerApp';
var G_BackupFolderName = 'Backup';
var G_DataFolderName = 'Data'
var G_FolderPath = '';
var G_FullImageListDiary = [];
var G_SelectedListOfImages = '';
var G_ServerURL = 'https://smartexpenditure.com/' /*  */
var G_Content = '';


var G_GENERALEntryKey = 0;


/* Calendar Related */
var G_today = new Date();
var G_TodayMonth = G_today.getMonth() +1 ;
var G_TodayYear = G_today.getFullYear();
var G_TodaysCalendarID = -1;

var G_chosenYear = 2016;
var G_chosenMonth = 2;
var G_chosenNextYear = 2017;
var G_chosenNextMonth = 3;
var G_chosenPrevYear = 2015;
var G_chosenPrevMonth = 1;
var G_CustomStartDate = new Date();
var G_CustomEndDate = new Date();
var G_CustomNextStartDate = new Date();
var G_CustomNextEndDate = new Date();
var G_CustomPrevStartDate = new Date();
var G_CustomPrevEndDate = new Date();
var G_NextDay = '20160103';
var G_SelectedDay = '20160325';
var G_PrevDay = '20160101';


var G_monthFullNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
var G_monthShortNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
var G_dayFullNames = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
var G_dayShortNames = ['SUN','MON','TUE','WED','THU','FRI','SAT'];

var G_currentMonthDays = []; // list of 42 days related to selected month 






//expense related 
var G_selectedcategoryName = '';
var G_selectedColor = '';
var G_selectedIcon = '';
var G_CategoriesAction = '';
var G_SelectedExpenseCategoryID = 0;
var G_SelectedIncomeCategoryID = 0;
var G_SelectedTransactionKey = 0;

//initia setup related
G_InitialScreenPassed = 0;


//CURRENCY RELATED
var G_SelectedCurrency = 106;

//FIRST DAY OF WEEK RELATED
var G_SelectedFirstDayOfWeek = 1;

//PASSWORD RELATED
var G_SelectedPassword = '';
var G_TypedPassword = '';
var G_PasswordRecoveryEmail = '';
var G_InsertedPassword = '';
var G_PasswordAction = '';
var G_EntryScreenFromLocation = ''; // available values [fromMain] , [dayDetails]


//ENTRY RELATED
var G_NoteFirstView = 1;
var G_TransactionAmount = 0;
var G_TransactionAmountString = '0';
var G_EntryTransactionStep = 'focus';
var G_CurrentAmountOperation = '';
var G_TransactionType = 'expense';

var G_SelectedTransactionCategory = '-1';
var G_SelectedTransactionNote = '';
var G_SelectedTransactionRepeatCode = -1;


var G_BlankTransaction = {
		"transactionKey" : 0,
		"transactionAmount": 0,
		"transactionType": '',
		"transactionCategoryCode" : '',				
		"transactionNote" : '',
		"repeatCode": -1
	};

var G_BlankDayEntry ={
		"dateKey" : 0,
		"monthNr" : 0,
		"yearNr" : 0,
		"weekNr" : 0,
		"nrExpenseTransaction" : 0,
		"nrIncomeTransaction" : 0,
		"dayBalance" : 0,
		"transactionList" : []		
	}
	
var G_SelectedDayTransactionList = [];	
var G_FullEntryList = [];
var G_SelectedDayEntry = [];
var G_SelectedTransaction = [];
var G_SelectedTransactionArrayID = -1;
var G_SelectedDayEntryArrayID = -1;


//////////////////////
// CHART RELATED
/////////////////////
var G_SelectedTimeFrame = 'monthly'; //available values monthly / weekly / yearly
var G_ChartSelectedMonth = 1;
var G_ChartSelectedWeek = 1;
var G_ChartSelectedYear = 2016;

var G_ChartSelectedNextMonth = 1;
var G_ChartSelectedNextWeek = 1;
var G_ChartSelectedNextYear = 2016;

var G_ChartSelectedPrevMonth = 1;
var G_ChartSelectedPrevWeek = 1;
var G_ChartSelectedPrevYear = 2016;
var G_ChartType = '';


//////////////////////
// REMINDER RELATED
/////////////////////
var G_ReminderName = '';
var G_ReminderRepeatsEveryNumber = 1;
var G_ReminderTimeOfTheDay = 12;
var G_ReminderRepeatsEveryPeriod = 'day'; // available values : day | week | month
var G_ReminderStartDate = new Date();
var G_RemindersList = [];
var G_repeatingPeriodsDef = {'day':'Day', 'week':'Week','month':'Month' }
var G_ReminderAction = 'new';
var G_SelectedReminderID = -1;
var G_EveryDayReminderHour = 20;
var G_EveryDayReminderEnabled = 1;
var G_CurrentDetailsScreen = '';
var G_CurrentDetailsScreenFromInit = '';



var G_NumberOfAppStarts = 0;
var G_PToChange = '';
var G_NewP = '';



/////////////////
//LANGUAGE
/////////////////
var G_CurrentLanguage = 'EN';
var G_Translations = {};


