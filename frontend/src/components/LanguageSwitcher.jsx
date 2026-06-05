import { useTranslation } from 'react-i18next';
import { Globe } from 'lucide-react';

const LanguageSwitcher = () => {
  const { i18n, t } = useTranslation();

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
  };

  const currentLanguage = i18n.language?.split('-')[0] || 'de';

  return (
    <label className="flex min-h-11 w-full items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-700 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-200">
      <Globe className="w-4 h-4 text-gray-500 shrink-0" />
      <span className="truncate text-xs font-medium text-gray-500">{t('language.label')}</span>
      <select
        value={currentLanguage}
        onChange={(e) => changeLanguage(e.target.value)}
        className="ml-auto min-h-8 rounded bg-transparent text-sm font-medium text-gray-800 dark:text-gray-100"
        aria-label={t('language.select')}
      >
        <option value="de">{t('language.de')}</option>
        <option value="en">{t('language.en')}</option>
      </select>
    </label>
  );
};

export default LanguageSwitcher;
