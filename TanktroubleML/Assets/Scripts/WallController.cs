﻿using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class WallController : MonoBehaviour
{

    // Start is called before the first frame update
    void Start()
    {
        
    }

    public Vector2Int LevelPos;


    // Update is called once per frame
    void Update()
    {

    }

    void OnMouseOver() {
        if (Input.GetMouseButton(1))
            transform.parent.GetComponent<LevelCreator>().RemoveWall(LevelPos);
        
    }
}
