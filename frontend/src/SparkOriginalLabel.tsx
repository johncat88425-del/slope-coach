import {Localize,useLanguage} from './i18n.js';

/** The API supplies these Spark fields in English; never translate their contents. */
export function SparkOriginalLabel(){
 if(useLanguage()!=='zh')return null;
 return <Localize><small className="spark-original-label" data-testid="spark-original-label" lang="zh-Hant">Muse Spark original (English)</small></Localize>;
}
