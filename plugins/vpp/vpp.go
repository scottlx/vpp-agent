//  Copyright (c) 2019 Cisco and/or its affiliates.
//
//  Licensed under the Apache License, Version 2.0 (the "License");
//  you may not use this file except in compliance with the License.
//  You may obtain a copy of the License at:
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
//  Unless required by applicable law or agreed to in writing, software
//  distributed under the License is distributed on an "AS IS" BASIS,
//  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//  See the License for the specific language governing permissions and
//  limitations under the License.

package vpp

import (
	"errors"
	"fmt"

	govppapi "git.fd.io/govpp.git/api"
	"github.com/ligato/cn-infra/logging"

	"go.ligato.io/vpp-agent/v3/plugins/vpp/binapi"
)

var (
	// ErrIncompatible is an error returned when no compatible handler is found.
	ErrIncompatible = errors.New("incompatible handler")
	// ErrNoVersions is an error returned when no handler versions are found.
	ErrNoVersions = errors.New("no handler versions")
	// ErrPluginDisabled is an error returned when disabled plugin is detected.
	ErrPluginDisabled = errors.New("plugin not available")
)

type Version = binapi.Version

// Client provides methods for managing VPP.
type Client interface {
	CompatibilityChecker

	// NewAPIChannel returns new channel for sending binapi requests.
	NewAPIChannel() (govppapi.Channel, error)
	// Stats provides access to VPP stats API.
	Stats() govppapi.StatsProvider
	// IsPluginLoaded returns true if the given plugin is currently loaded.
	IsPluginLoaded(plugin string) bool
}

type CompatibilityChecker interface {
	// CheckCompatiblity checks compatibility with given binapi messages.
	CheckCompatiblity(...govppapi.Message) error
}

func FindCompatibleBinapi(ch CompatibilityChecker) (binapi.Version, error) {
	if len(binapi.Versions) == 0 {
		return "", fmt.Errorf("no binapi versions loaded")
	}
	logging.Debugf("checking compatibility for %d binapi versions", len(binapi.Versions))
	for version, msgList := range binapi.Versions {
		msgs := msgList.AllMessages()
		if err := ch.CheckCompatiblity(msgs...); err == nil {
			logging.Debugf("found compatible binapi version: %v", version)
			return version, nil
		} else if ierr, ok := err.(*govppapi.CompatibilityError); ok {
			logging.Debugf("binapi version %-15v incompatible: %d/%d incompatible messages", version, len(ierr.IncompatibleMessages), len(msgs))
		} else {
			logging.Warnf("binapi version %v check failed: %v", version, err)
		}
	}
	return "", fmt.Errorf("no compatible binapi version found")
}