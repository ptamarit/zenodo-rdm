// This file is part of Zenodo.
// Copyright (C) 2023 CERN.
//
// Zenodo is free software; you can redistribute it
// and/or modify it under the terms of the GNU General Public License as
// published by the Free Software Foundation; either version 2 of the
// License, or (at your option) any later version.
//
// Zenodo is distributed in the hope that it will be
// useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Zenodo; if not, write to the
// Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
// MA 02111-1307, USA.
//
// In applying this license, CERN does not
// waive the privileges and immunities granted to it by virtue of its status
// as an Intergovernmental Organization or submit itself to any jurisdiction.

import React from "react";
import { PropTypes } from "prop-types";
import { Button } from "semantic-ui-react";
import { withState } from "react-searchkit";

export const LayoutSwitchButtons = withState(
  ({ updateQueryState, currentQueryState, currentLayout, onLayoutChange }) => {
    const handleLayoutChange = (layout) => {
      const numOfRecords = layout === "grid" ? 12 : 6;
      updateQueryState({ ...currentQueryState, size: numOfRecords });
      onLayoutChange(layout);
    };

    return (
      <Button.Group>
        <Button
          icon="th"
          name="grid"
          active={currentLayout === "grid"}
          onClick={() => handleLayoutChange("grid")}
          aria-label="Grid view"
        />
        <Button
          icon="th list"
          name="list"
          active={currentLayout === "list"}
          onClick={() => handleLayoutChange("list")}
          aria-label="List view"
        />
      </Button.Group>
    );
  }
);

LayoutSwitchButtons.propTypes = {
  currentLayout: PropTypes.string.isRequired,
  onLayoutChange: PropTypes.func.isRequired,
  updateQueryState: PropTypes.func.isRequired,
  currentQueryState: PropTypes.object.isRequired,
};
