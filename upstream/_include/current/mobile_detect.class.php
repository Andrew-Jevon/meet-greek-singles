<?php

/* (C) Websplosion LLC, 2001-2021

  IMPORTANT: This is a commercial software product
  and any kind of using it must agree to the Websplosion's license agreement.
  It can be found at http://www.chameleonsocial.com/license.doc

  This notice may not be removed from the source code. */

class mobile_detect extends Mobile_Detect_Base {

    protected static $cacheProperties = '';

    public function setUserAgent($userAgent = null)
    {
        if (!empty($userAgent)) {
            $this->userAgent = $userAgent;
        } else {

            $this->userAgent = null;

            foreach ($this->getUaHttpHeaders() as $altHeader) {
                if (!empty($this->httpHeaders[$altHeader])) { // @todo: should use getHttpHeader(), but it would be slow. (Serban)
                    $this->userAgent .= $this->httpHeaders[$altHeader] . " ";
                }
            }

            $this->userAgent = (!empty($this->userAgent) ? trim($this->userAgent) : null);
        }
        self::$cacheProperties .= $this->userAgent;
        return $this->userAgent;
    }

    public function isMobile($userAgent = null, $httpHeaders = null)
    {
        if ($httpHeaders) {
            $this->setHttpHeaders($httpHeaders);
        }

        if ($userAgent) {
            $this->setUserAgent($userAgent);
        }
        $currentProperties = get_session('browser_version_cache');
        $isMobile = get_session('is_mobile_browser', null);

        if ($currentProperties == $this->getCacheProperties() && $isMobile !== null) {
            return get_session('is_mobile_browser');
        }
        $this->setDetectionType(self::DETECTION_TYPE_MOBILE);

        if ($this->checkHttpHeadersForMobile()) {
            $result = true;
        } else {
            $result = $this->matchDetectionRulesAgainstUA();
        }

        set_session('is_mobile_browser', $result);
        return $result;
    }

    public function isTablet($userAgent = null, $httpHeaders = null)
    {
        $currentProperties = get_session('browser_version_cache');
        $isTablet = get_session('is_tablet_browser', null);
        if ($currentProperties == $this->getCacheProperties() && $isTablet !== null) {
            return get_session('is_tablet_browser');
        }
        $this->setDetectionType(self::DETECTION_TYPE_MOBILE);

        foreach (self::$tabletDevices as $_regex) {
            if ($this->match($_regex, $userAgent)) {
                set_session('is_tablet_browser', true);
                return true;
            }
        }
        set_session('is_tablet_browser', false);
        return false;
    }

    public function isMobileNoTablet()
    {
        $result = ($this->isMobile() && !$this->isTablet()) ? true : false;
        set_session('browser_version_cache', $this->getCacheProperties());
        set_session('is_mobile_no_tablet_browser', $result);
        return $result;
    }

    public function getCacheProperties()
    {
        return md5(self::$cacheProperties);
    }

}
