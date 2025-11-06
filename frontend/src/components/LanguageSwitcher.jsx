import { useTranslation } from 'react-i18next';
import { Globe } from 'lucide-react';

const LanguageSwitcher = () => {
  const { i18n, t } = useTranslation();

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
  };

  const currentLanguage = i18n.language;

  return (
    <div className="relative group">
      <button
        className="flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
        aria-label={t('language.select')}
      >
        <Globe className="w-4 h-4" />
        <span className="font-medium">{currentLanguage.toUpperCase()}</span>
      </button>
      <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
        <div className="py-1">
          <button
            onClick={() => changeLanguage('en')}
            className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-100 transition-colors ${
              currentLanguage === 'en' ? 'bg-blue-50 text-blue-600 font-medium' : 'text-gray-700'
            }`}
          >
            {t('language.en')}
          </button>
          <button
            onClick={() => changeLanguage('de')}
            className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-100 transition-colors ${
              currentLanguage === 'de' ? 'bg-blue-50 text-blue-600 font-medium' : 'text-gray-700'
            }`}
          >
            {t('language.de')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default LanguageSwitcher;
