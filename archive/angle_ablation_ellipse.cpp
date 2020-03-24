float v_angle = egGeometryUtils::angleFromFirst2SecondVector(v_offset, v_xDir);

            Vector3d v_axis = egGeometryUtils::computePerpendicularAxis(v_offset, v_xDir);

            const TransMatrix3d v_RotMatrix = TransMatrix3d::makeRotate(v_axis, v_angle);
v_offset is calculated as:
            Vector3d v_offset = (v_targetPoint - v_entryPoint);
            v_offset.normalize(v_offset.length());

v_xDir:
v_xDir[0] = 1;
            v_xDir[1] = 0;
            v_xDir[2] = 0;
