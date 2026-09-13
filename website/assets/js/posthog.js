/* PostHog web snippet — https://posthog.com/docs/product-analytics/installation/web */
(function () {
  var TOKEN = "phc_CVJu8dpCfdmKyRaxhrYPQURCb4YnyM3Qzu6jniSu2Cc6";
  var HOST = "https://us.i.posthog.com";
  if (!TOKEN) return;

  !function(t,e){var o,n,p,r;e.__SV||(window.posthog && window.posthog.__loaded)||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}p||((p=t.createElement("script")).type="text/javascript",p.crossOrigin="anonymous",p.async=!0,p.src=s.api_host.replace(".i.posthog.com","-assets.i.posthog.com")+"/static/array.js",p.onerror=function(){p=null},(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r));var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],Object.defineProperty(u,"toString",{configurable:!0,enumerable:!0,writable:!0,value:function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e}}),Object.defineProperty(u.people,"toString",{configurable:!0,enumerable:!0,writable:!0,value:function(){return u.toString(1)+".people (stub)"}}),o="init capture register register_once register_for_session unregister unregister_for_session getFeatureFlag getFeatureFlagResult isFeatureEnabled reloadFeatureFlags updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures on onFeatureFlags onSessionId getSurveys getActiveMatchingSurveys renderSurvey canRenderSurvey getNextSurveyStep identify setPersonProperties group resetGroups setPersonPropertiesForFlags resetPersonPropertiesForFlags setGroupPropertiesForFlags resetGroupPropertiesForFlags reset get_distinct_id getGroups get_session_id get_session_replay_url alias set_config startSessionRecording stopSessionRecording sessionRecordingStarted captureException loadToolbar get_property getSessionProperty createPersonProfile opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing clear_opt_in_out_capturing debug".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);

  function pageGroup(pathname) {
    var p = (pathname || "").toLowerCase();
    if (p.indexOf("/pages/how-it-was-formed") !== -1) return "How it was formed";
    if (p.indexOf("/pages/quickstart") !== -1) return "Quick Start";
    if (p.indexOf("/pages/browse-app") !== -1) return "Browse Apps";
    if (p.indexOf("/pages/task") !== -1) return "Tasks";
    if (p.indexOf("/marketing/clips") !== -1) return "Clips";
    if (
      p === "/androidlife" ||
      p === "/androidlife/" ||
      p.indexOf("/androidlife/index.html") !== -1
    ) {
      return "Home";
    }
    return "Other";
  }

  posthog.init(TOKEN, {
    api_host: HOST,
    defaults: "2026-05-30",
  });
  posthog.register({
    site: "androidlife",
    page_group: pageGroup(window.location.pathname),
  });
})();
